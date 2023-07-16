import data_converter
from video_downloaders.yt_downloader import YouTubeDownloader
from video_downloaders.bili_downloader import BiliBiliDownloader
import subprocess
import file_util
from sql.sql_handler import SQLHandler
from tqdm import tqdm
import discord_webhook
import argparse

CONFIG = file_util.read_config("config.ini")


def rclone_to_cloud():
    """
    Uploads all files in the download_output_path to the cloud
    """
    subprocess.run(
        f'{CONFIG.get("path","rclone_path")} -P copy "{CONFIG.get("path","download_output_path")}" "{CONFIG.get("path","rclone_cloud_target")}"',
        shell=True,
    )
    subprocess.run(f'{CONFIG.get("path","rclone_path")} -P copy "{CONFIG.get("path","thumbnail_output_path")}" "{CONFIG.get("path","rclone_thumbnail_target")}"', shell=True)


def download_and_upload():
    """
    Downloads videos from the download_list.txt file and uploads them to the cloud
    (optional) sends a message to discord webhook
    """
    file_util.clear_output_folder(
        CONFIG.get("path", "download_output_path")
    )
    file_util.clear_output_folder(CONFIG.get("path", "thumbnail_output_path"))
    yt_downloader = YouTubeDownloader(CONFIG.get("path", "download_output_path"))
    bili_downloader = BiliBiliDownloader(CONFIG.get("path", "download_output_path"), cookies=CONFIG.get("queue", "bilibili_cookies"))


    for url in tqdm(file_util.read_file("download_list.txt")):
        if "youtube" in url:
            try:
                yt_downloader.download_urls(url)
            except Exception as e:
                print("Error downloading youtube video:", e)
                return
        elif "bilibili" in url:
            bili_downloader.download_urls(url)
    if not len(list(data_converter.get_all_files_in_directory(CONFIG.get("path", "download_output_path")))):
        print("No videos downloaded. Skipping conversion...")
        return
    data_converter.convert_all_mkv_to_webm(
        CONFIG.get("path", "download_output_path")
    )
    data_converter.convert_all_mp4_to_webm(
        CONFIG.get("path", "download_output_path")
    )
    rclone_to_cloud()
    update_database()
    discord_webhook.send_completed_message(CONFIG.get("discord", "webhook"), ["https://www.youtube.com/watch?v="+video_id.replace(".webm", "") for video_id in list(data_converter.get_all_files_in_directory("output_video", "webm"))])
    file_util.clear_output_folder(
        CONFIG.get("path", "download_output_path"))
    file_util.clear_output_folder(CONFIG.get("path", "thumbnail_output_path"))


def main():
    parser = argparse.ArgumentParser(description='Archiving Worker Script')
    parser.add_argument('--archive', type=str, help='URL to archive')
    parser.add_argument('--no-download', action='store_true', help='Optional flag')
    args = parser.parse_args()
    if args.archive is not None:
        with open("download_list.txt", "w") as f:
            f.write(args.archive + "\n")
    if not args.no_download:
        download_and_upload()

def execute_server_worker(url: str):
    """
    To be executed through server.py when deploying an automatic archival
    """
    with open("download_list.txt", "w") as f:
        f.write(url + "\n")
    download_and_upload()


def update_database():
    hostname = CONFIG.get("database", "host")
    user = CONFIG.get("database", "user")
    password = CONFIG.get("database", "password")
    database = CONFIG.get("database", "database")
    ssh_host = CONFIG.get("database", "ssh_host")
    ssh_username = CONFIG.get("database", "ssh_username")
    ssh_password = CONFIG.get("database", "ssh_password")
    remote_bind = CONFIG.get("database", "remote_bind")
    if ssh_host == "" or ssh_username == "" or ssh_password == "":
        print("No or Invalid SSH credentials provided. Skipping...")
        ssh_host = None
        ssh_username = None
        ssh_password = None
    server = SQLHandler(hostname, user, password, database, ssh_host, ssh_username, ssh_password, remote_bind)
    # server.create_table("songs", "video_id VARCHAR(255) PRIMARY KEY, title TEXT, channel_name VARCHAR(255), channel_id VARCHAR(255), upload_date VARCHAR(255), description TEXT")
    headers = "video_id, title, channel_name, channel_id, upload_date, description"
    for video_data in tqdm(data_converter.generate_database_row_data("download_list.txt")):
        if server.insert_row("songs", headers, (video_data["video_id"], video_data["title"], video_data["channel_name"], video_data["channel_id"], video_data["upload_date"], video_data["description"])) is False:
            break
    server.close_connection()

if __name__ == "__main__":
    main()
