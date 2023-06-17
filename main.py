import data_converter
from yt_downloader import YouTubeDownloader
import subprocess
import os
import json

OUTPUT_PATH = "C:\\Users\\donal\\OneDrive\\Documents\\Covers-Archive-Worker\\output_video"
TARGET_CLOUD_PATH = "Cloudflare R2:vtuber-rabbit-hole-archive/VTuber Covers Archive"
RCLONE_PATH = "C:\\Users\\donal\\OneDrive\\Documents\\Covers-Archive-Worker\\rclone-v1.62.2-windows-amd64\\rclone.exe"


def rclone_to_cloud():
    subprocess.run(f'{RCLONE_PATH} -P copy "{OUTPUT_PATH}" "{TARGET_CLOUD_PATH}"')

def clear_output_folder(file_path: str = OUTPUT_PATH):
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
        data_converter.convert_all_mkv_to_webm(OUTPUT_PATH)
    print("Download Complete... Ready to generate csv data (y/n)")
    data_converter.generate_json_data("output_video", ".webm") if input() == "y" else print("Skipping...")
    print("JSON Data Generated... Upload to Cloud? (y/n)")
    rclone_to_cloud() if input() == "y" else print("Skipping...")



if __name__ == "__main__":
    main()
