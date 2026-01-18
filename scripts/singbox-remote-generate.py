import json
import argparse
import os
import requests


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


def replace_outbounds_in_fixed_target(source_data, config_path, output_file):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"基础配置文件 '{config_path}' 未找到")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            target_data = json.load(f)
    except json.JSONDecodeError:
        print(f"🎃读取配置文件时发生错误，请检查内容格式 (路径: {config_path})")
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
                if outbound["outbounds"] is None:
                    outbound["outbounds"] = []
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
        print(f"✅处理完成，文件已保存至：{os.path.abspath(output_file)}")
    except IOError as e:
        print(f"🎃保存文件时发生错误：{e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="通过 URL 或本地文件合并到本地 sing-box 配置"
    )
    parser.add_argument(
        "-u", "--url", required=True, help="订阅链接 (JSON URL) 或本地 JSON 文件路径"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="生成后的配置文件保存路径"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="singbox-config/config-android-open.json",
        help="基础模板路径",
    )

    args = parser.parse_args()

    if not os.path.isabs(args.output):
        args.output = os.path.join(os.getcwd(), args.output)

    try:
        print(f"正在从模板加载：{args.config}")

        if os.path.isfile(args.url):
            print(f"检测到本地文件，正在读取：{args.url}")
            with open(args.url, "r", encoding="utf-8") as f:
                source_data = json.load(f)
        else:
            print(f"正在下载订阅数据：{args.url}")
            source_data = download_json_from_url(args.url)

        replace_outbounds_in_fixed_target(source_data, args.config, args.output)

    except Exception as e:
        print(f"🎃运行出错：{e}")


if __name__ == "__main__":
    main()
