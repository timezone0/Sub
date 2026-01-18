import requests
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

url = "https://github.com/sub-store-org/Sub-Store/releases/latest/download/sub-store.bundle.js"
local_filename = os.path.basename(url)

with requests.get(url, stream=True) as r:
    r.raise_for_status()
    with open(local_filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

print(f"✅ 下载完成: {local_filename}")
