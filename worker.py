from video_downloaders.yt_downloader import YouTubeDownloader
import subprocess
import file_util
from sql.sql_handler import SQLHandler
import discord_webhook
import os
from video_types import VideoType
import shutil
from archive_api import ArchiveAPI
from datetime import datetime

CONFIG = file_util.read_config("config.ini")

def write_debug_log(message: str) -> None:
    """
    Prints a message to the standard output with a timestamp
    :param message: str
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def rclone_to_cloud():
    """
    Uploads all files in output folder to respective S3 bucket locations
    """
    write_debug_log("Preparing to upload files to cloud...")
    write_debug_log("Upload video file to cloud using rclone")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} -P copy "{CONFIG.get("path","output_dir")}/video" "{CONFIG.get("path","rclone_video_target")}"', shell=True)
    write_debug_log("Upload thumbnail file to cloud using rclone")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} -P copy "{CONFIG.get("path","output_dir")}/thumbnail" "{CONFIG.get("path","rclone_thumbnail_target")}"', shell=True)
    write_debug_log("Upload metadata file to cloud using rclone")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} -P copy "{CONFIG.get("path","output_dir")}/metadata" "{CONFIG.get("path","rclone_metadata_target")}"', shell=True)
    write_debug_log("Upload captions to cloud using rclone")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} -P copy "{CONFIG.get("path","output_dir")}/captions" "{CONFIG.get("path","rclone_captions_target")}"', shell=True)

def update_database(video_data: dict):
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
    headers = "video_id, title, channel_name, channel_id, upload_date, description"
    if server.insert_row("songs", headers, (video_data["video_id"], video_data["title"], video_data["channel_name"], video_data["channel_id"], video_data["upload_date"], video_data["description"])) is False:
        write_debug_log("Error inserting row into database")
        return
    server.close_connection()

def archive_video(url: str):
    """
    Runs through the full routine of downloading a video, thumbnail, metadata, and captions
    """
    write_debug_log(f"New task received: {url} || Beginning archival...")
    archiver_api = ArchiveAPI()
    if archiver_api.video_is_archived(url):
        write_debug_log("Video is already archived. Skipping...")
        return
    if os.path.exists(CONFIG.get("path", "output_dir")):
        shutil.rmtree(CONFIG.get("path", "output_dir"))
    def classify_video_type() -> tuple:
        """
        Classifies the video type based on the URL
        :return: VideoType
        """
        if "youtube.com" in url:
            return VideoType.YOUTUBE, YouTubeDownloader(CONFIG.get("path", "output_dir"))
        elif "bilibili.com" in url:
            # stub. TODO: re-implement Bilibili support with new protocol and project structure
            write_debug_log("Bilibili support is currently disabled")
            return None
            # return VideoType.BILIBILI
        else:
            return None
    video_type  = classify_video_type()[0]
    video_downloader = classify_video_type()[1]
    write_debug_log("Classified video type as " + video_type.name)
    video_downloader.download_video(url, "webm")
    video_downloader.download_thumbnail(url)
    video_metadata_dict = video_downloader.download_metadata(url)
    update_database(video_metadata_dict)
    video_downloader.download_captions(url)

def execute_server_worker(url: str):
    """
    To be executed through server.py when deploying an automatic archival
    """
    archive_video(url)
    rclone_to_cloud()
    discord_webhook.send_completed_message(CONFIG.get("discord", "webhook"), url)

if __name__ == "__main__":
    pass
