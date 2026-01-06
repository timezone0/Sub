import os
import sys
import time
import socket
import requests
import subprocess
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, session
import argparse

# 切换到主脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

# === 命令行参数解析 ===
parser = argparse.ArgumentParser(description="Flask 后端 + SubStore 配置生成器")
parser.add_argument("--mihomo-dir", default="../mihomo", help="Mihomo 输出目录")
parser.add_argument("--singbox-dir", default="../singbox", help="Singbox 输出目录")
args, _ = parser.parse_known_args()

MIHOMO_DIR = args.mihomo_dir
SINGBOX_DIR = args.singbox_dir

# 配置文件存放目录（相对于 app-web.py）
MIHOMO_CONFIG_DIR = "scripts/mihomo-config"
SINGBOX_CONFIG_DIR = "scripts/singbox-config"

# === 基础配置 ===
SUBSTORE_PORT = 3002
SUBSTORE_HOST = "127.0.0.1"
API_BASE = f"http://{SUBSTORE_HOST}:{SUBSTORE_PORT}"

app = Flask(__name__)
app.secret_key = "your-secret-key"

# === 实用函数 ===
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def encode_gitlab_url(raw_url):
    return raw_url.replace("%", "%25").replace("%", "%25")

def get_config_files(directory, extension):
    """扫描指定目录下的配置文件"""
    if not os.path.exists(directory):
        return []
    return sorted([f for f in os.listdir(directory) if f.endswith(extension)])

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
        return "✅ 缓存刷新成功"
    except Exception as e:
        return f"❌ 缓存刷新失败：{e}"

def generate_configs(name, url, mihomo_tpl, singbox_tpl):
    logs = [f"▶ 正在处理订阅：{name}"]

    # URL 编码处理
    encoded_url = (
        encode_gitlab_url(url)
        if url.startswith("https://gitlab.com/api/")
        else quote(url, safe="")
    )
    local_url = f"{API_BASE}/download/sub?url={encoded_url}"

    # 获取当前工作目录的绝对路径
    base_abs_path = os.path.dirname(os.path.abspath(__file__))

    # 核心修复：将输出路径和模板路径全部转换为绝对路径，防止子脚本 chdir 后找不到文件
    mihomo_out = os.path.abspath(os.path.join(MIHOMO_DIR, f"{name}.yaml"))
    singbox_out = os.path.abspath(os.path.join(SINGBOX_DIR, f"{name}.json"))
    
    mihomo_tpl_path = os.path.abspath(os.path.join(base_abs_path, MIHOMO_CONFIG_DIR, mihomo_tpl))
    singbox_tpl_path = os.path.abspath(os.path.join(base_abs_path, SINGBOX_CONFIG_DIR, singbox_tpl))

    # 调用 Mihomo 脚本 (-u, -o, -c 参数)
    logs.append(f"▶ 正在生成 Mihomo 配置 (模板: {mihomo_tpl})...")
    result1 = subprocess.run(
        ["python", "scripts/mihomo-remote-generate.py", "-u", local_url, "-o", mihomo_out, "-c", mihomo_tpl_path],
        capture_output=True,
        text=True,
    )
    logs.append(result1.stdout.strip() if result1.returncode == 0 else f"❌ Mihomo 错误:\n{result1.stderr.strip()}")

    # 调用 Singbox 脚本 (-u, -o, -c 参数)
    logs.append(f"▶ 正在生成 Singbox 配置 (模板: {singbox_tpl})...")
    result2 = subprocess.run(
        ["python", "scripts/singbox-remote-generate.py", "-u", local_url, "-o", singbox_out, "-c", singbox_tpl_path],
        capture_output=True,
        text=True,
    )
    logs.append(result2.stdout.strip() if result2.returncode == 0 else f"❌ Singbox 错误:\n{result2.stderr.strip()}")

    return logs

# === Flask 路由 ===
@app.route("/", methods=["GET", "POST"])
def index():
    mihomo_configs = get_config_files(MIHOMO_CONFIG_DIR, ".yaml")
    singbox_configs = get_config_files(SINGBOX_CONFIG_DIR, ".json")

    if request.method == "POST":
        name = request.form.get("name")
        url = request.form.get("url")
        mihomo_tpl = request.form.get("mihomo_tpl")
        singbox_tpl = request.form.get("singbox_tpl")
        
        logs = []
        if name and url:
            logs.append(refresh_backend())
            logs += generate_configs(name, url, mihomo_tpl, singbox_tpl)
        else:
            logs.append("❌ 名称和 URL 不能为空")

        session["temp_data"] = {
            "name": name, 
            "url": url, 
            "logs": logs,
            "mihomo_tpl": mihomo_tpl,
            "singbox_tpl": singbox_tpl
        }
        return redirect(url_for("index"))

    temp_data = session.pop("temp_data", {})
    return render_template(
        "index.html",
        name=temp_data.get("name", ""),
        url=temp_data.get("url", ""),
        logs=temp_data.get("logs", []),
        mihomo_configs=mihomo_configs,
        singbox_configs=singbox_configs,
        sel_mihomo=temp_data.get("mihomo_tpl", "config-android.yaml"),
        sel_singbox=temp_data.get("singbox_tpl", "config-android.json")
    )

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_substore_backend()
    app.run(debug=True, port=5002)
