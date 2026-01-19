import requests
import os
import sys

try:
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
except Exception as e:
    print(f"❌ 切换目录失败: {e}")

url = "https://github.com/sub-store-org/Sub-Store/releases/latest/download/sub-store.bundle.js"
local_filename = os.path.basename(url)

try:
    print(f"正在下载: {url} ...")

    with requests.get(url, stream=True, timeout=15) as r:
        r.raise_for_status()

        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print(f"✅ 下载完成: {local_filename}")

except requests.exceptions.HTTPError as errh:
    print(f"❌ HTTP 错误: {errh}")
except requests.exceptions.ConnectionError:
    print("❌ 连接错误: 请检查网络或代理设置。")
except requests.exceptions.Timeout:
    print("❌ 超时错误: 服务器响应太慢。")
except requests.exceptions.RequestException as err:
    print(f"❌ 请求异常: {err}")
except IOError as e:
    print(f"❌ 文件写入失败 (IOError): {e}")
except Exception as e:
    print(f"❌ 发生未知错误: {e}")
