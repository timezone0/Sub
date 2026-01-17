import os
import time
import socket
import requests
import subprocess
import threading
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, session
import argparse
from http.server import SimpleHTTPRequestHandler, HTTPServer
from typing import Optional

# === 基础目录与变量定义 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MIHOMO_CONFIG_REL_DIR = "scripts/mihomo-config"
SINGBOX_CONFIG_REL_DIR = "scripts/singbox-config"


# === 新增：清理逻辑 ===
def cleanup_uploads(max_age_seconds: int = 60):
    """清理上传目录中超过指定时间的旧文件（默认1分钟）"""
    try:
        now = time.time()
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path) and filename.startswith("up_"):
                if os.stat(file_path).st_mtime < now - max_age_seconds:
                    os.remove(file_path)
    except Exception as e:
        print(f"⚠️ 清理上传目录失败: {e}")


# === 参数解析 ===
parser = argparse.ArgumentParser()
parser.add_argument("--mihomo-dir", default="mihomo")
parser.add_argument("--singbox-dir", default="singbox")
args, _ = parser.parse_known_args()

MIHOMO_DIR = os.path.abspath(os.path.join(BASE_DIR, args.mihomo_dir))
SINGBOX_DIR = os.path.abspath(os.path.join(BASE_DIR, args.singbox_dir))
os.makedirs(MIHOMO_DIR, exist_ok=True)
os.makedirs(SINGBOX_DIR, exist_ok=True)

# === 配置 ===
SUBSTORE_PORT = 3002
SUBSTORE_HOST = "127.0.0.1"
API_BASE = f"http://{SUBSTORE_HOST}:{SUBSTORE_PORT}"
TEMP_HTTP_PORT = 18888

app = Flask(__name__)
app.secret_key = "final_stable_key"


# === 实用工具 ===
def encode_gitlab_url(raw_url: str) -> str:
    """处理 GitLab API URL 的特殊编码需求"""
    return raw_url.replace("%", "%25").replace("%", "%25")


def refresh_backend() -> str:
    """刷新 Sub-Store 后端资源缓存"""
    try:
        res = requests.get(f"{API_BASE}/api/utils/refresh", timeout=5)
        res.raise_for_status()
        return "✅ Sub-Store 缓存刷新成功"
    except Exception as e:
        return f"⚠️ 缓存刷新失败 (不影响生成): {e}"


# === 临时 HTTP 服务（闭包版本） ===
def run_temporary_server(file_path: str, port: int) -> Optional[HTTPServer]:
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
            _ = (format, args)
            pass

    try:
        server = HTTPServer(("127.0.0.1", port), SingleFileHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server
    except Exception as e:
        print(f"❌ 启动临时 HTTP 服务失败: {e}")
        return None


# === 其他工具函数 ===
def get_config_files(directory_rel: str, extension: str) -> list[str]:
    abs_dir = os.path.join(BASE_DIR, directory_rel)
    if not os.path.exists(abs_dir):
        return []
    return sorted([f for f in os.listdir(abs_dir) if f.endswith(extension)])


def wait_for_port(host: str, port: int, timeout: int = 10) -> bool:
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
        return
    try:
        subprocess.Popen(
            ["node", os.path.join(BASE_DIR, "substore/sub-store.bundle.js")],
            env={
                **os.environ,
                "SUB_STORE_BACKEND_API_PORT": str(SUBSTORE_PORT),
                "SUB_STORE_DATA_BASE_PATH": os.path.join(BASE_DIR, "substore"),
            },
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_for_port(SUBSTORE_HOST, SUBSTORE_PORT)
    except Exception as e:
        print(f"❌ 启动 SubStore 后端失败: {e}")


def generate_configs(
    name: str, url_or_path: str, mihomo_tpl: str, singbox_tpl: str
) -> list[str]:
    logs: list[str] = [f"▶ 正在处理: {name}"]
    temp_server: Optional[HTTPServer] = None

    # 判断是本地文件还是 URL
    if os.path.isfile(url_or_path):
        temp_server = run_temporary_server(os.path.abspath(url_or_path), TEMP_HTTP_PORT)
        if temp_server:
            target_url = quote(f"http://127.0.0.1:{TEMP_HTTP_PORT}/sub", safe="")
            logs.append("📂 已挂载本地文件服务")
        else:
            target_url = quote(url_or_path, safe="")
    else:
        target_url = (
            encode_gitlab_url(url_or_path)
            if url_or_path.startswith("https://gitlab.com/api/")
            else quote(url_or_path, safe="")
        )

    substore_proxy_url = f"{API_BASE}/download/sub?url={target_url}"

    m_out = os.path.abspath(os.path.join(MIHOMO_DIR, f"{name}.yaml"))
    s_out = os.path.abspath(os.path.join(SINGBOX_DIR, f"{name}.json"))
    m_tpl_path = os.path.abspath(
        os.path.join(BASE_DIR, MIHOMO_CONFIG_REL_DIR, mihomo_tpl)
    )
    s_tpl_path = os.path.abspath(
        os.path.join(BASE_DIR, SINGBOX_CONFIG_REL_DIR, singbox_tpl)
    )

    os.makedirs(os.path.dirname(m_out), exist_ok=True)
    os.makedirs(os.path.dirname(s_out), exist_ok=True)

    try:
        logs.append(f"▶ 正在生成 Mihomo (模板: {mihomo_tpl})...")
        r1 = subprocess.run(
            [
                "python",
                os.path.join(BASE_DIR, "scripts/mihomo-remote-generate.py"),
                "-u",
                substore_proxy_url,
                "-o",
                m_out,
                "-c",
                m_tpl_path,
            ],
            capture_output=True,
            text=True,
        )
        if r1.stdout:
            logs.extend([f"   [Mihomo LOG] {line}" for line in r1.stdout.splitlines()])
        success_m = (r1.returncode == 0) and ("🎃" not in r1.stdout)
        logs.append("✅ Mihomo 执行完成" if success_m else "❌ Mihomo 执行失败")

        logs.append(f"▶ 正在生成 Singbox (模板: {singbox_tpl})...")
        r2 = subprocess.run(
            [
                "python",
                os.path.join(BASE_DIR, "scripts/singbox-remote-generate.py"),
                "-u",
                substore_proxy_url,
                "-o",
                s_out,
                "-c",
                s_tpl_path,
            ],
            capture_output=True,
            text=True,
        )
        if r2.stdout:
            logs.extend([f"   [Singbox LOG] {line}" for line in r2.stdout.splitlines()])
        success_s = (r2.returncode == 0) and ("🎃" not in r2.stdout)
        logs.append("✅ Singbox 执行完成" if success_s else "❌ Singbox 执行失败")
    finally:
        if temp_server:
            temp_server.shutdown()
            temp_server.server_close()

    return logs


# === Flask 路由 ===
@app.route("/", methods=["GET", "POST"])
def index():
    mihomo_configs = get_config_files(MIHOMO_CONFIG_REL_DIR, ".yaml")
    singbox_configs = get_config_files(SINGBOX_CONFIG_REL_DIR, ".json")

    if request.method == "POST":
        cleanup_uploads(60)

        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        file = request.files.get("file_sub")
        m_tpl = request.form.get("mihomo_tpl", "config-android-open.yaml")
        s_tpl = request.form.get("singbox_tpl", "config-android-open.json")

        target_input: str = ""
        logs: list[str] = []

        if file and file.filename:
            safe_filename = f"up_{int(time.time())}_{file.filename}"
            path = os.path.join(UPLOAD_FOLDER, safe_filename)
            file.save(path)
            target_input = path
            url = ""
            if not name:
                # 确保 filename 为 str
                filename_only = file.filename or "upload"
                name = os.path.splitext(filename_only)[0]
            logs.append(f"✅ 使用上传文件: {file.filename}")
        elif url:
            target_input = url
            if not name:
                name = f"Sub_{int(time.time())}"
            logs.append("🔗 使用远程 URL")

        if target_input and name:
            logs.append(refresh_backend())
            logs += generate_configs(name, target_input, m_tpl, s_tpl)
        else:
            logs.append(
                "❌ 错误：未识别到有效输入，必须从两种输入方式中任选一种进行输入"
            )

        session["temp_data"] = {
            "name": name,
            "url": url,
            "logs": logs,
            "sel_mihomo": m_tpl,
            "sel_singbox": s_tpl,
        }
        return redirect(url_for("index"))

    d = session.pop("temp_data", {})
    return render_template(
        "index.html",
        name=d.get("name", ""),
        url=d.get("url", ""),
        logs=d.get("logs", []),
        sel_mihomo=d.get("sel_mihomo", "config-android-open.yaml"),
        sel_singbox=d.get("sel_singbox", "config-android-open.json"),
        mihomo_configs=mihomo_configs,
        singbox_configs=singbox_configs,
    )


# === 启动入口 ===
if __name__ == "__main__":
    os.chdir(BASE_DIR)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_substore_backend()
    app.run(debug=True, port=5002, host="0.0.0.0")