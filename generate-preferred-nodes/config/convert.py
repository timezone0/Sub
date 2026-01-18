import csv
import argparse
from ruamel.yaml import YAML


def export_proxies_to_csv(yaml_file, csv_file):
    yaml = YAML()

    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            config = yaml.load(f)

        proxies = config.get("proxies", [])

        header = ["IP地址", "端口", "地区"]

        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

            for p in proxies:
                ip = p.get("server", "")
                port = p.get("port", "")
                name = p.get("name", "")

                writer.writerow([ip, port, name])

        print(f"✅ 转换成功！源文件: {yaml_file} -> 输出文件: {csv_file}")

    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 '{yaml_file}'")
    except Exception as e:
        print(f"❌ 运行出错: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 Clash YAML 提取代理节点到 CSV")

    parser.add_argument(
        "-c", "--config", type=str, required=True, help="输入的 YAML 配置文件路径"
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="config.csv",
        help="输出的 CSV 文件路径 (默认: config.csv)",
    )

    args = parser.parse_args()

    export_proxies_to_csv(args.config, args.output)
