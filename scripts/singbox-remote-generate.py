import json
import argparse
import os
import requests

# 设置工作目录为脚本所在目录
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
        print(f"🎃解析 JSON 文件时发生错误，请确保 URL 提供的是有效的 JSON 数据 (URL：{url})")
        raise

def replace_outbounds_in_fixed_target(source_data, config_path, output_file):
    # 检查传入的模板配置文件是否存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"基础配置文件 '{config_path}' 未找到")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            target_data = json.load(f)
    except json.JSONDecodeError:
        print(f"🎃读取配置文件时发生错误，请检查内容格式 (路径: {config_path})")
        raise

    try:
        # 过滤掉不需要的类型和特定的加密方法
        skip_types = {"direct", "block", "dns", "urltest", "selector"}
        new_outbounds = [
            o
            for o in source_data.get("outbounds", [])
            if o.get("type") not in skip_types and o.get("method") != "chacha20"
        ]

        # 合并出站代理
        existing_outbounds = target_data.get("outbounds", [])
        target_data["outbounds"] = existing_outbounds + new_outbounds

        # 更新 selector 或 urltest 等组中的节点列表
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

    # 确保输出目录存在
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
    parser = argparse.ArgumentParser(description="通过 URL 下载 JSON 并合并到本地 sing-box 配置")
    
    # 将 url 改为可选参数 -u/--url，设置为必填
    parser.add_argument(
        "-u", "--url", 
        required=True, 
        help="订阅链接 (JSON 格式的 URL)"
    )
    
    # 将 output 改为可选参数 -o/--output，设置为必填
    parser.add_argument(
        "-o", "--output", 
        required=True, 
        help="生成后的配置文件保存路径"
    )
    
    # 基础模板配置路径保持不变
    parser.add_argument(
        "-c", "--config", 
        default="singbox-config/config-android.json", 
        help="基础模板配置文件路径 (默认: singbox-config/config-android.json)"
    )
    
    args = parser.parse_args()

    # 处理输出路径，如果不是绝对路径则基于当前工作目录
    if not os.path.isabs(args.output):
        args.output = os.path.join(os.getcwd(), args.output)

    try:
        print(f"正在从模板加载：{args.config}")
        print(f"正在下载订阅数据：{args.url}")
        
        source_data = download_json_from_url(args.url)
        replace_outbounds_in_fixed_target(source_data, args.config, args.output)
        
    except Exception as e:
        print(f"🎃运行出错：{e}")

if __name__ == "__main__":
    main()
