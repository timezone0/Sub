import os
import argparse
import requests

def download_live_file(url):
    # 1. 准备目录和路径
    target_dir = "live"
    file_name = "live.txt"
    file_path = os.path.join(target_dir, file_name)

    try:
        # 2. 检查并创建目录
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"[*] 已创建目录: {target_dir}")

        print(f"[*] 正在尝试从 {url} 下载...")

        # 3. 发起请求 (设置超时以防死等)
        response = requests.get(url, timeout=15, stream=True)
        
        # 检查 HTTP 状态码 (404, 500 等会抛出异常)
        response.raise_for_status()

        # 4. 写入文件
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"[+] 下载成功！文件已保存至: {file_path}")

    except requests.exceptions.HTTPError as e:
        print(f"[!] HTTP 错误: {e}")
    except requests.exceptions.ConnectionError:
        print("[!] 网络连接失败，请检查你的网络连接或 URL 是否正确。")
    except requests.exceptions.Timeout:
        print("[!] 请求超时，服务器响应太慢。")
    except PermissionError:
        print("[!] 权限错误：无法写入文件或创建目录。")
    except Exception as e:
        print(f"[!] 发生未知错误: {e}")

if __name__ == "__main__":
    # 使用 argparse 处理命令行参数
    parser = argparse.ArgumentParser(description="下载链接内容并保存至 live/live.txt")
    parser.add_argument("--url", required=True, help="需要下载的 URL 链接")
    
    args = parser.parse_args()

    # 执行下载
    download_live_file(args.url)