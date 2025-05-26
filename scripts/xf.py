import requests
import zipfile
import os
import sys

def download(url, output):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        print(f"下载失败：{e}")

def remove_lines_after_keyword(file_path, keyword):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            if keyword in line:
                lines = lines[:i]
                break

        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
    except Exception as e:
        print(f"处理文件失败：{e}")

def remove_lines_containing_url(file_path, url):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        lines = [line for line in lines if url not in line]

        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
    except Exception as e:
        print(f"删除包含URL的行失败：{e}")

def get_stb_id():
    try:
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        os.chdir(script_dir)

        parent_dir = os.path.dirname(script_dir)
        live_dir = os.path.join(parent_dir, 'live')
        if not os.path.exists(live_dir):
            os.makedirs(live_dir)

        zip_path = './iptv.zip'
        extract_path = live_dir

        download("http://api.y977.com/iptv.txt.zip", zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            if 'iptv.txt' in file_list:
                zip_ref.extract('iptv.txt', extract_path, pwd="xfflchVCWG9941".encode())
            else:
                print("未找到 iptv.txt")

        iptv_file_path = os.path.join(extract_path, 'iptv.txt')
        remove_lines_after_keyword(iptv_file_path, '卫视,#genre#')
        remove_lines_containing_url(iptv_file_path, "http://ottrrs.hl.chinamobile.com")

        if os.path.exists(zip_path):
            os.remove(zip_path)

    except Exception as e:
        print(f"解压失败：{e}")

def main():
    get_stb_id()

if __name__ == "__main__":
    main()