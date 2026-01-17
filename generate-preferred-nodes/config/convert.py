import csv
import argparse
from ruamel.yaml import YAML

def export_proxies_to_csv(yaml_file, csv_file):
    yaml = YAML()
    
    try:
        # 读取 YAML 文件
        with open(yaml_file, 'r', encoding='utf-8') as f:
            config = yaml.load(f)
        
        # 提取 proxies 节点信息
        proxies = config.get('proxies', [])
        
        # 准备 CSV 表头
        header = ['IP地址', '端口', '地区']
        
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            
            for p in proxies:
                # [span_0](start_span)对应提取: server->IP, port->端口, name->地区[span_0](end_span)
                ip = p.get('server', '')
                port = p.get('port', '')
                name = p.get('name', '')
                
                writer.writerow([ip, port, name])
                
        print(f"✅ 转换成功！源文件: {yaml_file} -> 输出文件: {csv_file}")

    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 '{yaml_file}'")
    except Exception as e:
        print(f"❌ 运行出错: {e}")

if __name__ == "__main__":
    # 配置命令行参数解析
    parser = argparse.ArgumentParser(description="从 Clash YAML 提取代理节点到 CSV")
    
    # 添加 -c / --config 参数
    parser.add_argument('-c', '--config', type=str, required=True, help="输入的 YAML 配置文件路径")
    
    # 添加可选的输出文件名参数，默认为 config.csv
    parser.add_argument('-o', '--output', type=str, default="config.csv", help="输出的 CSV 文件路径 (默认: config.csv)")
    
    args = parser.parse_args()
    
    # 执行函数
    export_proxies_to_csv(args.config, args.output)
