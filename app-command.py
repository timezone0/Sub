import os
import json
import time
import socket
import argparse
import requests
import subprocess
import threading
from urllib.parse import quote
from http.server import SimpleHTTPRequestHandler, HTTPServer

# === 配置 ===
SUBSTORE_PORT = 3003
SUBSTORE_HOST = "127.0.0.1"
API_BASE = f"http://{SUBSTORE_HOST}:{SUBSTORE_PORT}"
TEMP_HTTP_PORT = 18888  # 临时 HTTP 服务的端口，用于让 SubStore 读取本地文件


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


# === 临时 HTTP 服务（用于将本地文件映射为 URL） ===
def run_temporary_server(file_path, port):
    """开启一个只提供单个文件下载的轻量级 HTTP 服务器"""

    class SingleFileHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)

        def log_message(self, format, *args):
            _ = format, args
            pass

    try:
        server = HTTPServer(("127.0.0.1", port), SingleFileHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server
    except Exception as e:
        log(f"❌ 启动临时 HTTP 服务失败: {e}")
        return None


# === 实用函数 ===
def encode_gitlab_url(raw_url):
    return raw_url.replace("%", "%25")


def wait_for_port(host, port, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def start_substore_backend():
    if wait_for_port(SUBSTORE_HOST, SUBSTORE_PORT, timeout=1):
        log("✅ SubStore 后端已在运行")
        return

    env = os.environ.copy()
    env["SUB_STORE_BACKEND_API_PORT"] = str(SUBSTORE_PORT)
    env["SUB_STORE_DATA_BASE_PATH"] = "./substore"

    try:
        subprocess.Popen(
            ["node", "./substore/sub-store.bundle.js"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log("✅ SubStore 后端正在启动...")
        if wait_for_port(SUBSTORE_HOST, SUBSTORE_PORT):
            log("✅ SubStore 服务已就绪")
    except Exception as e:
        log(f"❌ 无法启动 SubStore: {e}")


def refresh_backend():
    try:
        log("▶ 正在刷新后端资源缓存...")
        res = requests.get(f"{API_BASE}/api/utils/refresh")
        res.raise_for_status()
        log("✅ 缓存刷新成功")
    except Exception as e:
        log(f"❌ 缓存刷新失败：{e}")


def handle_one(name, url, mihomo_dir, singbox_dir, mihomo_config, singbox_config):
    refresh_backend()
    log(f"▶ 正在处理：{name}")

    mihomo_out = os.path.abspath(os.path.join(mihomo_dir, f"{name}.yaml"))
    singbox_out = os.path.abspath(os.path.join(singbox_dir, f"{name}.json"))

    temp_server = None
    target_url = url

    if os.path.isfile(url):
        abs_path = os.path.abspath(url)
        log(f"📂 检测到本地文件: {abs_path}")
        temp_server = run_temporary_server(abs_path, TEMP_HTTP_PORT)
        if temp_server:
            target_url = f"http://127.0.0.1:{TEMP_HTTP_PORT}/local-file"
            log(f"🌐 已建立临时访问链接: {target_url}")

    mihomo_config_abs = os.path.abspath(mihomo_config)
    singbox_config_abs = os.path.abspath(singbox_config)

    encoded_url = (
        encode_gitlab_url(target_url)
        if target_url.startswith("https://gitlab.com/api/")
        else quote(target_url, safe="")
    )
    substore_url = f"{API_BASE}/download/sub?url={encoded_url}"

    try:
        log(f"▶ 正在生成 Mihomo 配置 (模板: {mihomo_config_abs})...")
        subprocess.run(
            [
                "python",
                "scripts/mihomo-remote-generate.py",
                "-u",
                substore_url,
                "-o",
                mihomo_out,
                "-c",
                mihomo_config_abs,
            ],
            check=True,
        )

        log(f"▶ 正在生成 Singbox 配置 (模板: {singbox_config_abs})...")
        subprocess.run(
            [
                "python",
                "scripts/singbox-remote-generate.py",
                "-u",
                substore_url,
                "-o",
                singbox_out,
                "-c",
                singbox_config_abs,
            ],
            check=True,
        )

    except subprocess.CalledProcessError as e:
        log(f"❌ {name} 处理失败: 脚本执行错误 {e}")
    except Exception as e:
        log(f"❌ {name} 发生未知错误: {e}")
    finally:
        if temp_server:
            temp_server.shutdown()
            temp_server.server_close()
            log("🛑 临时 HTTP 服务已关闭")

    print("-" * 30)


def handle_json(json_path, mihomo_dir, singbox_dir, mihomo_config, singbox_config):
    try:
        if json_path.startswith(("http://", "https://")):
            data = requests.get(json_path).json()
        else:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        for item in data:
            sub_name = item.get("name")
            sub_url = item.get("url")
            if sub_name and sub_url:
                handle_one(
                    sub_name,
                    sub_url,
                    mihomo_dir,
                    singbox_dir,
                    mihomo_config,
                    singbox_config,
                )
    except Exception as e:
        log(f"❌ 解析 JSON 列表失败: {e}")


# === 主程序入口 ===
if __name__ == "__main__":
    start_substore_backend()

    parser = argparse.ArgumentParser(description="SubStore 自动化配置生成工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", help="批量处理 JSON 文件路径或 URL")
    group.add_argument("--name", help="单条处理时的订阅名称")

    parser.add_argument("--url", help="单条处理时的订阅地址（支持本地路径或 URL）")
    parser.add_argument("--mihomo-dir", default="mihomo", help="Mihomo 输出目录")
    parser.add_argument("--singbox-dir", default="singbox", help="Singbox 输出目录")
    parser.add_argument(
        "--mihomo-config",
        default="scripts/mihomo-config/config-android-open.yaml",
        help="Mihomo 模板",
    )
    parser.add_argument(
        "--singbox-config",
        default="scripts/singbox-config/config-android-open.json",
        help="Singbox 模板",
    )

    args = parser.parse_args()

    for d in [args.mihomo_dir, args.singbox_dir]:
        if not os.path.exists(d):
            os.makedirs(d)

    if args.json:
        handle_json(
            args.json,
            args.mihomo_dir,
            args.singbox_dir,
            args.mihomo_config,
            args.singbox_config,
        )
    elif args.name and args.url:
        refresh_backend()
        handle_one(
            args.name,
            args.url,
            args.mihomo_dir,
            args.singbox_dir,
            args.mihomo_config,
            args.singbox_config,
        )
    else:
        log("❌ 缺少参数：使用 --name 时必须提供 --url")