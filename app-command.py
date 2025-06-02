import os
import json
import time
import socket
import argparse
import requests
import subprocess
from urllib.parse import quote

# === 配置 ===
SUBSTORE_PORT = 3003
SUBSTORE_HOST = "127.0.0.1"
API_BASE = f"http://{SUBSTORE_HOST}:{SUBSTORE_PORT}"

# 切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# === 实用函数 ===
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def encode_gitlab_url(raw_url):
    return raw_url.replace("%", "%25").replace("%", "%25")


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
        log("✅ SubStore 后端启动中，等待响应...")
        if wait_for_port(SUBSTORE_HOST, SUBSTORE_PORT):
            log("✅ SubStore 服务已就绪")
        else:
            log("⚠️ 等待超时，服务可能未成功启动")
    except Exception as e:
        log(f"❌ 启动 SubStore 后端失败：{e}")


def refresh_backend():
    try:
        log("▶ 正在刷新后端资源缓存...")
        res = requests.get(f"{API_BASE}/api/utils/refresh")
        res.raise_for_status()
        log("✅ 缓存刷新成功")
    except Exception as e:
        log(f"❌ 缓存刷新失败：{e}")

def get_output_paths(name, mihomo_dir, singbox_dir):
    return (
        os.path.join(mihomo_dir, f"{name}.yaml"),
        os.path.join(singbox_dir, f"{name}.json"),
    )


def handle_one(name, url, mihomo_dir, singbox_dir):
    log(f"▶ 开始处理订阅：{name}")

    encoded_url = (
        encode_gitlab_url(url)
        if url.startswith("https://gitlab.com/api/")
        else quote(url, safe="")
    )
    local_url = f"{API_BASE}/download/sub?url={encoded_url}"

    mihomo_out, singbox_out = get_output_paths(name, mihomo_dir, singbox_dir)

    try:
        log("▶ 正在生成 Mihomo 配置...")
        subprocess.run(
            ["python", "scripts/mihomo-remote-generate.py", local_url, mihomo_out],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log(f"❌ 生成 Mihomo 配置失败：{e}")

    try:
        log("▶ 正在生成 Singbox 配置...")
        subprocess.run(
            ["python", "scripts/singbox-remote-generate.py", local_url, singbox_out],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log(f"❌ 生成 Singbox 配置失败：{e}")

    log("-----------------------------")


def handle_json(json_input, mihomo_dir, singbox_dir):
    refresh_backend()

    try:
        if json_input.startswith("http://") or json_input.startswith("https://"):
            log(f"从网络加载 JSON：{json_input}")
            response = requests.get(json_input)
            response.raise_for_status()
            items = response.json()
        else:
            if not os.path.isfile(json_input):
                log("❌ 无效的 JSON 文件路径")
                return
            log(f"读取本地 JSON 文件：{json_input}")
            with open(json_input, "r", encoding="utf-8") as f:
                items = json.load(f)
    except Exception as e:
        log(f"❌ 加载 JSON 失败：{e}")
        return

    for item in items:
        name = item.get("name")
        url = item.get("url")
        if name and url:
            handle_one(name, url, mihomo_dir, singbox_dir)
        else:
            log(f"⚠️ 跳过无效项：{item}")


# === 主程序入口 ===
if __name__ == "__main__":
    start_substore_backend()

    parser = argparse.ArgumentParser(description="生成 Mihomo 和 Singbox 配置")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", help="JSON 文件路径或 URL（包含 name/url）")
    group.add_argument("--name", help="订阅名称（需配合 --url）")
    parser.add_argument("--url", help="订阅地址")
    parser.add_argument("--mihomo-dir", default="../mihomo", help="Mihomo 配置输出目录")
    parser.add_argument(
        "--singbox-dir", default="../singbox", help="Singbox 配置输出目录"
    )

    args = parser.parse_args()

    if args.json:
        handle_json(args.json, args.mihomo_dir, args.singbox_dir)
    elif args.name and args.url:
        refresh_backend()
        handle_one(args.name, args.url, args.mihomo_dir, args.singbox_dir)
    else:
        log("❌ 参数不完整，请使用 --json 或 --name 与 --url")

