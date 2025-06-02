import requests
import os
import sys
import argparse
import re
import ruamel.yaml
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def download_yaml(url):
    try:
        headers = {"User-Agent": "clash.meta"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"🎃下载 YAML 文件时发生错误 (URL：{url})：{e}")
        raise


def preprocess_yaml(yaml_content):
    try:
        content = re.sub(r"!\<str\>", "", yaml_content)
        return content
    except re.error as e:
        print(f"🎃预处理 YAML 内容时发生错误：{e}")
        raise


def extract_proxies(yaml_content):
    try:
        yaml_content = preprocess_yaml(yaml_content)
        yaml = ruamel.yaml.YAML(typ="rt")
        data = yaml.load(yaml_content)
        proxies = data.get("proxies", [])

        name_count = {}
        for proxy in proxies:
            if "name" in proxy:
                name = proxy["name"]
                if name in name_count:
                    name_count[name] += 1
                    proxy["name"] = f"{name}_{name_count[name]}"
                else:
                    name_count[name] = 0

        return proxies
    except Exception as e:
        print(f"🎃提取代理时发生错误：{e}")
        raise


def load_config(config_path):
    try:
        yaml = ruamel.yaml.YAML(typ="rt")
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.load(file)
    except FileNotFoundError:
        print(f"🎃未找到配置文件：{config_path}")
        raise
    except ruamel.yaml.YAMLError as e:
        print(f"🎃加载配置文件时发生错误：{e}")
        raise
    except Exception as e:
        print(f"🎃读取配置文件时发生未知错误：{e}")
        raise


def insert_proxies_to_config(config_data, proxies):
    try:
        proxy_groups_index = None
        for idx, key in enumerate(config_data.keys()):
            if key == "proxy-groups":
                proxy_groups_index = idx
                break

        if proxy_groups_index is not None:
            items = list(config_data.items())
            items.insert(proxy_groups_index, ("proxies", proxies))
            config_data.clear()
            config_data.update(dict(items))
        else:
            config_data["proxies"] = proxies
        return config_data
    except Exception as e:
        print(f"🎃插入代理到配置文件时发生错误：{e}")
        raise


def insert_names_into_proxy_groups(config_data):
    try:
        proxies = config_data.get("proxies", [])
        proxy_groups = config_data.get("proxy-groups", [])

        proxy_names = [proxy.get("name") for proxy in proxies if "name" in proxy]
        excluded_names = ["🎯 全球直连", "🛑 全球拦截", "🍃 应用净化"]

        for group in proxy_groups:
            if "proxies" in group:
                if group.get("name") not in excluded_names:
                    if not group["proxies"]:
                        group["proxies"] = proxy_names
                    else:
                        group["proxies"].extend(proxy_names)

        return config_data
    except Exception as e:
        print(f"🎃更新代理组时发生错误：{e}")
        raise


def apply_quotes_to_strings(data):
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = apply_quotes_to_strings(value)
        elif isinstance(data, list):
            return [apply_quotes_to_strings(item) for item in data]
        elif isinstance(data, str):
            return DoubleQuotedScalarString(data)
        return data
    except Exception as e:
        print(f"🎃应用双引号时发生错误：{e}")
        raise


def save_result(config_data, result_path):
    try:
        dir_name = os.path.dirname(result_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        yaml = ruamel.yaml.YAML(typ="rt")
        yaml.width = float("inf")
        config_data = apply_quotes_to_strings(config_data)
        with open(result_path, "w", encoding="utf-8") as file:
            yaml.dump(config_data, file)
    except IOError as e:
        print(f"🎃保存文件时发生错误：{e}")
        raise
    except Exception as e:
        print(f"🎃保存结果时发生未知错误：{e}")
        raise


def main(url, result_path):
    try:
        print(f"正在下载 YAML 文件：{url}")
        yaml_content = download_yaml(url)
        proxies = extract_proxies(yaml_content)

        config_path = "mihomo-config/config.yaml"
        config_data = load_config(config_path)

        updated_config = insert_proxies_to_config(config_data, proxies)
        updated_config = insert_names_into_proxy_groups(updated_config)

        save_result(updated_config, result_path)
        print(f"✅处理完成，文件已保存到：{ os.path.abspath(result_path) }")
    except Exception as e:
        print(f"🎃执行脚本时发生错误：{e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="通过 URL 下载 YAML 文件")
    parser.add_argument("url", help="需要下载的 YAML 文件的 URL ")
    parser.add_argument("result_path", help="保存结果的路径")
    args = parser.parse_args()

    main(args.url, args.result_path)