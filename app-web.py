import os
import sys
import time
import socket
import requests
import subprocess
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, session

# === 基础配置 ===
SUBSTORE_PORT = 3002
SUBSTORE_HOST = "127.0.0.1"
API_BASE = f"http://{SUBSTORE_HOST}:{SUBSTORE_PORT}"
MIHOMO_DIR = "../mihomo"
SINGBOX_DIR = "../singbox"

# 切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

app = Flask(__name__)
app.secret_key = "your-secret-key"


# === 实用函数 ===
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def encode_gitlab_url(raw_url):
    # GitLab API 特殊处理：需要对 `%` 进行双重编码
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
        log(f"❌ 启动 SubStore 后端失败: {e}")


def refresh_backend():
    try:
        log("刷新后端缓存...")
        res = requests.get(f"{API_BASE}/api/utils/refresh")
        res.raise_for_status()
        return "✅ 缓存刷新成功"
    except Exception as e:
        return f"❌ 缓存刷新失败: {e}"


def generate_configs(name, url):
    logs = [f"▶ 处理订阅: {name}"]

    encoded_url = (
        encode_gitlab_url(url)
        if url.startswith("https://gitlab.com/api/")
        else quote(url, safe="")
    )
    local_url = f"{API_BASE}/download/sub?url={encoded_url}"

    mihomo_out = os.path.join(MIHOMO_DIR, f"{name}.yaml")
    singbox_out = os.path.join(SINGBOX_DIR, f"{name}.json")

    # Mihomo 配置生成
    logs.append("▶ 生成 Mihomo 配置...")
    result1 = subprocess.run(
        ["python", "scripts/mihomo-remote-generate.py", local_url, mihomo_out],
        capture_output=True,
        text=True,
    )
    if result1.stdout.strip():
        logs.append(result1.stdout.strip())
    if result1.stderr.strip():
        logs.append("❌ Mihomo 错误：")
        logs.append(result1.stderr.strip())

    # Singbox 配置生成
    logs.append("▶ 生成 Singbox 配置...")
    result2 = subprocess.run(
        ["python", "scripts/singbox-remote-generate.py", local_url, singbox_out],
        capture_output=True,
        text=True,
    )
    if result2.stdout.strip():
        logs.append(result2.stdout.strip())
    if result2.stderr.strip():
        logs.append("❌ Singbox 错误：")
        logs.append(result2.stderr.strip())

    return logs


# === Flask 路由 ===
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        url = request.form.get("url")
        logs = []

        if name and url:
            logs.append(refresh_backend())
            logs += generate_configs(name, url)
        else:
            logs.append("❌ 名称和 URL 不能为空")

        session["temp_data"] = {"name": name, "url": url, "logs": logs}
        return redirect(url_for("index"))

    temp_data = session.pop("temp_data", {})
    return render_template(
        "index.html",
        name=temp_data.get("name", ""),
        url=temp_data.get("url", ""),
        logs=temp_data.get("logs", []),
    )


# === 主程序入口 ===
if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_substore_backend()
    app.run(debug=True, port=5002)

