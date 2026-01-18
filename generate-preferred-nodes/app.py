import csv
import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="根据 CSV 数据和 TXT 模板生成配置文件。"
    )

    parser.add_argument("--csv", required=True, help="输入的 CSV 配置文件路径")
    parser.add_argument("--txt", required=True, help="输入的模板 TXT 文件路径")
    parser.add_argument("--output", required=True, help="生成的输出文件路径")

    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv)
    txt_path = os.path.abspath(args.txt)
    output_path = os.path.abspath(args.output)

    if not os.path.exists(csv_path):
        print(f"❌ 错误: 找不到 CSV 文件 {csv_path}")
        sys.exit(1)
    if not os.path.exists(txt_path):
        print(f"❌ 错误: 找不到模板文件 {txt_path}")
        sys.exit(1)

    try:
        with open(csv_path, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
    except Exception as e:
        print(f"❌ 读取 CSV 出错: {e}")
        sys.exit(1)

    with open(txt_path, "r", encoding="utf-8") as template_file:
        template = template_file.read().strip()

    output_lines = []
    for row in rows:
        ip = (row.get("IP地址") or "0.0.0.0").strip()
        port = (row.get("端口") or "0").strip()
        name = (row.get("地区") or "未知").strip()

        line = (
            template.replace("%IP%", ip).replace("%PORT%", port).replace("%NAME%", name)
        )
        output_lines.append(line)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write("\n".join(output_lines))

    print(f"✅ 处理完成！已生成 {len(output_lines)} 条记录到: {output_path}")


if __name__ == "__main__":
    main()
