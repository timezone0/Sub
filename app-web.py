from flask import Flask, render_template, request, redirect, url_for, session
import subprocess
import os
import requests
from urllib.parse import quote
import sys

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

app = Flask(__name__)
app.secret_key = "your-secret-key"

API_BASE = "http://127.0.0.1:3002"
MIHOMO_DIR = "../mihomo"
SINGBOX_DIR = "../singbox"


def encode_gitlab_url(raw_url):
    encoded = raw_url.replace("%", "%25")
    encoded = encoded.replace("%", "%25")
    return encoded


def start_substore_backend():
    env = os.environ.copy()
    env["SUB_STORE_BACKEND_API_PORT"] = "3002"
    env["SUB_STORE_DATA_BASE_PATH"] = "./substore"

    try:
        subprocess.Popen(
            ["node", "./substore/sub-store.bundle.js"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✅ SubStore 后端已启动")
    except Exception as e:
        print(f"❌ 启动 SubStore 后端失败: {e}")


def refresh_backend():
    try:
        res = requests.get(f"{API_BASE}/api/utils/refresh")
        res.raise_for_status()
        return "缓存刷新成功"
    except Exception as e:
        return f"缓存刷新失败: {e}"


def generate_configs(name, url):
    if url.startswith("https://gitlab.com/api/"):
        encoded_url = encode_gitlab_url(url)
    else:
        encoded_url = quote(url, safe="")

    local_url = f"{API_BASE}/download/sub?url={encoded_url}"

    mihomo_out = os.path.join(MIHOMO_DIR, f"{name}.yaml")
    singbox_out = os.path.join(SINGBOX_DIR, f"{name}.json")

    logs = [f"处理订阅: {name}"]

    logs.append("▶ 生成 Mihomo 配置...")
    result1 = subprocess.run(
        ["python", "scripts/mihomo-remote-generate.py", local_url, mihomo_out],
        capture_output=True,
        text=True,
    )
    logs.append(result1.stdout.strip())
    if result1.stderr:
        logs.append("Mihomo 错误输出：")
        logs.append(result1.stderr.strip())

    logs.append("▶ 生成 Singbox 配置...")
    result2 = subprocess.run(
        ["python", "scripts/singbox-remote-generate.py", local_url, singbox_out],
        capture_output=True,
        text=True,
    )
    logs.append(result2.stdout.strip())
    if result2.stderr:
        logs.append("Singbox 错误输出：")
        logs.append(result2.stderr.strip())

    return logs


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        url = request.form.get("url")
        logs = []
        if name and url:
            msg = refresh_backend()
            logs.append(msg)
            logs += generate_configs(name, url)
        else:
            logs.append("名称和 URL 不能为空")

        session["temp_data"] = {"name": name, "url": url, "logs": logs}
        return redirect(url_for("index"))

    temp_data = session.pop("temp_data", {})
    name = temp_data.get("name", "")
    url = temp_data.get("url", "")
    logs = temp_data.get("logs", [])

    return render_template("index.html", logs=logs, name=name, url=url)


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_substore_backend()
    app.run(debug=True, port=5002)