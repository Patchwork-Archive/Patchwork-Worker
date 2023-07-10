import data_converter
from yt_downloader import YouTubeDownloader
import subprocess
import file_util
from sql.sql_handler import SQLHandler
from tqdm import tqdm
import discord_webhook
import sys

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


def download_and_upload(confirmations=False):
    """
    Downloads videos from the download_list.txt file and uploads them to the cloud
    (optional) sends a message to discord webhook
    """
    if confirmations:
        print("Clear output folder? (y/n)")
        file_util.clear_output_folder(
            CONFIG.get("path", "download_output_path")
        ) if input() == "y" else print("Skipping...")
        file_util.clear_output_folder(CONFIG.get("path", "thumbnail_output_path"))
        print("Download Videos? (y/n)")
        downloader = YouTubeDownloader(
            "download_list.txt", CONFIG.get("path", "download_output_path")
        )
        if input() == "y":
            downloader.download_urls()
            data_converter.convert_all_mkv_to_webm(
                CONFIG.get("path", "download_output_path")
            )
        print("Upload to Cloud? (y/n)")
        rclone_to_cloud() if input() == "y" else print("Skipping...")
        print("Ready to add to DB? (y/n)")
        update_database() if input() == "y" else print("Skipping...")
    else:
        file_util.clear_output_folder(
            CONFIG.get("path", "download_output_path")
        )
        file_util.clear_output_folder(CONFIG.get("path", "thumbnail_output_path"))
        downloader = YouTubeDownloader(
            "download_list.txt", CONFIG.get("path", "download_output_path")
        )
        downloader.download_urls()
        data_converter.convert_all_mkv_to_webm(
            CONFIG.get("path", "download_output_path")
        )
        rclone_to_cloud()
        update_database()
    discord_webhook.send_completed_message(CONFIG.get("discord", "webhook"), ["https://www.youtube.com/watch?v="+video_id.replace(".webm", "") for video_id in list(data_converter.get_all_files_in_directory("output_video", "webm"))])
    file_util.clear_output_folder(
        CONFIG.get("path", "download_output_path"))
    file_util.clear_output_folder(CONFIG.get("path", "thumbnail_output_path"))


def main():
    if not "--no-download" in sys.argv:
        download_and_upload(confirmations=False)


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
    for video_data in tqdm(data_converter.generate_database_row_data("output_video", "webm")):
        if server.insert_row("songs", headers, (video_data["video_id"], video_data["title"], video_data["channel_name"], video_data["channel_id"], video_data["upload_date"], video_data["description"])) is False:
            break
    server.close_connection()

if __name__ == "__main__":
    main()
