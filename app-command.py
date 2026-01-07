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

# 设置工作目录为脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# === 实用函数 ===
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def encode_gitlab_url(raw_url):
    """处理 GitLab 特殊 URL 编码"""
    return raw_url.replace("%", "%25")


def wait_for_port(host, port, timeout=10):
    """等待端口就绪"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def start_substore_backend():
    """启动 SubStore 后端"""
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
    """刷新后端缓存"""
    try:
        log("▶ 正在刷新后端资源缓存...")
        res = requests.get(f"{API_BASE}/api/utils/refresh")
        res.raise_for_status()
        log("✅ 缓存刷新成功")
    except Exception as e:
        log(f"❌ 缓存刷新失败：{e}")


def get_output_paths(name, mihomo_dir, singbox_dir):
    """生成输出文件的绝对路径"""
    return (
        os.path.abspath(os.path.join(mihomo_dir, f"{name}.yaml")),
        os.path.abspath(os.path.join(singbox_dir, f"{name}.json")),
    )


def handle_one(name, url, mihomo_dir, singbox_dir, mihomo_config, singbox_config):
    """处理单个订阅并传递所有必要参数"""
    log(f"▶ 开始处理订阅：{name}")

    # --- 新增：将模板路径转换为绝对路径 ---
    mihomo_config_abs = os.path.abspath(mihomo_config)
    singbox_config_abs = os.path.abspath(singbox_config)
    # ------------------------------------

    encoded_url = (
        encode_gitlab_url(url)
        if url.startswith("https://gitlab.com/api/")
        else quote(url, safe="")
    )
    local_url = f"{API_BASE}/download/sub?url={encoded_url}"

    mihomo_out, singbox_out = get_output_paths(name, mihomo_dir, singbox_dir)

    # 生成 Mihomo 配置
    try:
        log(f"▶ 正在生成 Mihomo 配置 (模板: {mihomo_config_abs})...") # 这里打印绝对路径方便排查
        subprocess.run(
            [
                "python", "scripts/mihomo-remote-generate.py",
                "-u", local_url,
                "-o", mihomo_out,
                "-c", mihomo_config_abs  # 使用绝对路径
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log(f"❌ 生成 Mihomo 配置失败：{e}")

    # 生成 Singbox 配置
    try:
        log(f"▶ 正在生成 Singbox 配置 (模板: {singbox_config_abs})...") # 这里打印绝对路径方便排查
        subprocess.run(
            [
                "python", "scripts/singbox-remote-generate.py",
                "-u", local_url,
                "-o", singbox_out,
                "-c", singbox_config_abs  # 使用绝对路径
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log(f"❌ 生成 Singbox 配置失败：{e}")

    log("-----------------------------")


def handle_json(json_input, mihomo_dir, singbox_dir, mihomo_config, singbox_config):
    """批量处理 JSON 中的项"""
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
            handle_one(name, url, mihomo_dir, singbox_dir, mihomo_config, singbox_config)
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
    
    # 增加对不同模板路径的支持
    parser.add_argument("--mihomo-dir", default="mihomo", help="Mihomo 配置输出目录")
    parser.add_argument("--singbox-dir", default="singbox", help="Singbox 配置输出目录")
    parser.add_argument(
        "--mihomo-config", 
        default="scripts/mihomo-config/config-android.yaml", 
        help="Mihomo 基础模板路径"
    )
    parser.add_argument(
        "--singbox-config", 
        default="scripts/singbox-config/config-android.json", 
        help="Singbox 基础模板路径"
    )

    args = parser.parse_args()

    # 统一调用参数
    if args.json:
        handle_json(args.json, args.mihomo_dir, args.singbox_dir, args.mihomo_config, args.singbox_config)
    elif args.name and args.url:
        refresh_backend()
        handle_one(args.name, args.url, args.mihomo_dir, args.singbox_dir, args.mihomo_config, args.singbox_config)
    else:
        log("❌ 参数错误: 使用 --name 时必须配合 --url")
