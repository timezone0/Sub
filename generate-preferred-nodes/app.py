import csv
import sys
import os

def main():
    # 获取脚本所在目录
    # base_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) != 4:
        print("用法: python app.py <config.csv> <config.txt> <output.txt>")
        sys.exit(1)

    # 拼接 CSV 和模板路径
    # csv_path = os.path.join(base_dir, sys.argv[1])
    # txt_path = os.path.join(base_dir, sys.argv[2])
    csv_path = os.path.abspath(sys.argv[1])
    txt_path = os.path.abspath(sys.argv[2])
    output_path = os.path.abspath(sys.argv[3])  # 输出路径可以是任意目录

    if not os.path.exists(csv_path):
        print(f"错误: 找不到文件 {csv_path}")
        sys.exit(1)
    if not os.path.exists(txt_path):
        print(f"错误: 找不到文件 {txt_path}")
        sys.exit(1)

    # 读取 CSV 文件
    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    # 读取模板文件
    with open(txt_path, "r", encoding="utf-8") as template_file:
        template = template_file.read().strip()

    # 生成结果
    output_lines = []
    for row in rows:
        ip = (row.get("IP地址") or "0.0.0.0").strip()
        port = (row.get("端口") or "0").strip()
        name = (row.get("地区") or "未知").strip()
        line = (
            template
            .replace("%IP%", ip)
            .replace("%PORT%", port)
            .replace("%NAME%", name)
        )
        output_lines.append(line)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 写入输出文件
    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write("\n".join(output_lines))

    print(f"✅ 已生成 {len(output_lines)} 条记录到 {output_path}")

if __name__ == "__main__":
    main()