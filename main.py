import data_converter
from yt_downloader import YouTubeDownloader
import subprocess
import os
import json
import file_util

CONFIG = file_util.read_config("C:\\Users\\donal\\OneDrive\\Desktop\Covers-Worker\\config.ini")

def rclone_to_cloud():
    subprocess.run(f'{CONFIG.get("rclone_path")} -P copy "{CONFIG.get("path","download_output_path")}" "{CONFIG.get("path","rclone_cloud_target")}"')

def clear_output_folder(file_path: str = CONFIG.get("path","download_output_path")):
    for file in os.listdir(file_path):
        os.remove(f"{file_path}\\{file}")

def verify_ndjson():
    with open("CoversArchive/covers.ndjson", "r", encoding="utf-8") as f:
        for line in f:
            try:
                x = json.loads(line)
                if x["video_id"] == "lvDNdCBcKJE":
                    print(x)
            except json.JSONDecodeError:
                print("Invalid JSON line: ", line)
                return False

def main():
    print("Clear output folder? (y/n)")
    clear_output_folder() if input() == "y" else print("Skipping...")
    print("Download Videos? (y/n)")
    downloader = YouTubeDownloader("download_list.txt")
    if input() == "y":
        downloader.download_urls()
        data_converter.convert_all_mkv_to_webm(CONFIG.get("path","download_output_path"))
    print("Download Complete... Ready to generate csv data (y/n)")
    data_converter.generate_json_data("output_video", ".webm") if input() == "y" else print("Skipping...")
    print("JSON Data Generated... Upload to Cloud? (y/n)")
    rclone_to_cloud() if input() == "y" else print("Skipping...")



if __name__ == "__main__":
    main()
