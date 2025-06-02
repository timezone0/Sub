import json
import argparse
import os
import requests

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def download_json_from_url(url):
    try:
        headers = {"User-Agent": "sing-box"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"🎃下载 JSON 文件时发生网络错误 (URL：{url})：{e}")
        raise
    except json.JSONDecodeError:
        print(
            f"🎃解析 JSON 文件时发生错误，请确保 URL 提供的是有效的 JSON 数据 (URL：{url})"
        )
        raise


def replace_outbounds_in_fixed_target(source_data, output_file):
    target_file = "singbox-config/config-1.12.json"
    if not os.path.exists(target_file):
        raise FileNotFoundError(f"配置文件 '{target_file}' 未找到")
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            target_data = json.load(f)
    except FileNotFoundError:
        print(f"🎃未找到配置文件：{target_file}")
        raise
    except json.JSONDecodeError:
        print(
            f"🎃读取配置文件时发生错误，请检查配置文件内容是否有效 (文件路径: {target_file})"
        )
        raise

    try:
        skip_types = {"direct", "block", "dns", "urltest", "selector"}

        new_outbounds = [
            o
            for o in source_data.get("outbounds", [])
            if o.get("type") not in skip_types and o.get("method") != "chacha20"
        ]

        existing_outbounds = target_data.get("outbounds", [])
        target_data["outbounds"] = existing_outbounds + new_outbounds

        for outbound in target_data["outbounds"]:
            if "outbounds" in outbound:
                for new_outbound in new_outbounds:
                    if new_outbound["tag"] not in outbound["outbounds"]:
                        outbound["outbounds"].append(new_outbound["tag"])

    except Exception as e:
        print(f"🎃替换 outbounds 时发生错误：{e}")
        raise

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(target_data, f, indent=2, ensure_ascii=False)
        print(f"✅处理完成，文件已保存到：{os.path.abspath(output_file)}")
    except IOError as e:
        print(f"🎃保存文件时发生错误：{e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="通过 URL 下载 JSON 文件")
    parser.add_argument("url", help="需要下载的 JSON 文件的 URL ")
    parser.add_argument("output", help="保存结果的路径")
    args = parser.parse_args()

    if not os.path.dirname(args.output):
        args.output = os.path.join(os.getcwd(), args.output)

    try:
        print(f"正在下载 JSON 文件：{args.url}")
        source_data = download_json_from_url(args.url)
        replace_outbounds_in_fixed_target(source_data, args.output)
    except FileNotFoundError as e:
        print(f"🎃文件操作时发生错误：{e}")
    except requests.exceptions.RequestException as e:
        print(f"🎃网络请求时发生错误：{e}")
    except json.JSONDecodeError as e:
        print(f"🎃JSON 解析时发生错误：{e}")
    except Exception as e:
        print(f"🎃处理过程中发生未知错误：{e}")


if __name__ == "__main__":
    main()