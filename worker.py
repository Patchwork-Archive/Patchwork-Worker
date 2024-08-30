from video_downloaders.yt_downloader import YouTubeDownloader
from video_downloaders.bili_downloader import BiliDownloader
import channel_meta_archiver
import subprocess
import file_util
from sql.sql_handler import SQLHandler
import discord_webhook
import os
from video_types import VideoType
import shutil
from archive_api import ArchiveAPI
from datetime import datetime
import cutlet

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

def rclone_channel_images_to_cloud(pfp_path: str, banner_path: str):
    """
    Uploads all channel images in output folder to respective S3 bucket locations
    """
    write_debug_log("Preparing to upload channel images to cloud...")
    write_debug_log("Upload banner file to cloud using rclone")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} -P copy "{banner_path}" "{CONFIG.get("path","rclone_banner_target")}"', shell=True)
    write_debug_log("Upload pfp file to cloud using rclone")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} -P copy "{pfp_path}" "{CONFIG.get("path","rclone_pfp_target")}"', shell=True)
    os.remove(pfp_path)
    os.remove(banner_path)

def update_database(video_data: dict, video_type: VideoType, file_ext: str, file_size: float):
    hostname = CONFIG.get("database", "host")
    user = CONFIG.get("database", "user")
    password = CONFIG.get("database", "password")
    database = CONFIG.get("database", "database")
    server = SQLHandler(hostname, user, password, database)
    headers = "video_id, title, channel_name, channel_id, upload_date, description"
    if server.check_row_exists("songs", "video_id", video_data["video_id"]):
        write_debug_log("Video already exists in database. Updating row instead...")
        server.execute_query(f"UPDATE songs SET title = '{video_data['title']}', channel_name = '{video_data['channel_name']}', channel_id = '{video_data['channel_id']}', upload_date = '{video_data['upload_date']}', description = '{video_data['description']}' WHERE video_id = '{video_data['video_id']}'")
    else: 
        if server.insert_row("songs", headers, (video_data["video_id"], video_data["title"], video_data["channel_name"], video_data["channel_id"], video_data["upload_date"], video_data["description"])) is False:
            write_debug_log("Error inserting row into database")
            return
    if server.insert_row("files", "video_id, size_mb, extension", (video_data["video_id"], file_size, file_ext)) is False:
        write_debug_log("Error inserting file data into database")
        return
    katsu = cutlet.Cutlet()
    romanized_title = katsu.romaji(video_data["title"])
    if server.insert_row("romanized", "video_id, romanized_title", (video_data["video_id"], romanized_title)) is False:
        write_debug_log("Error inserting romanization into database")
    if server.check_row_exists("channels", "channel_id", video_data["channel_id"]) is False and video_type == VideoType.YOUTUBE:
        channel_data = channel_meta_archiver.download_youtube_banner_pfp_desc(video_data["channel_id"], CONFIG.get("youtube", "api_key"))
        romanized_name = katsu.romaji(channel_data.name)
        rclone_channel_images_to_cloud(channel_data.pfp, channel_data.banner)
        server.insert_row("channels", "channel_id, channel_name, romanized_name, description", (video_data["channel_id"], channel_data.name, romanized_name, channel_data.description))
    if server.check_row_exists("channels", "channel_id", video_data["channel_id"]) is False and video_type == VideoType.BILIBILI:
        print("[WARNING] Bilibili Channel Meta Description not supported yet!")
    server.close_connection()

def archive_video(url: str, mode: int)->bool:
    """
    Runs through the full routine of downloading a video, thumbnail, metadata, and captions
    :param url: str
    :param force: int - 0 for normal archival, 1 for force archival
    """
    write_debug_log(f"New task received: {url} || Beginning archival...")
    if os.path.exists(CONFIG.get("path", "output_dir")):
        shutil.rmtree(CONFIG.get("path", "output_dir"))
    def classify_video_type() -> tuple:
        """
        Classifies the video type based on the URL
        :return: VideoType
        """
        if "youtube.com" in url or "youtu.be" in url:
            return VideoType.YOUTUBE, YouTubeDownloader(CONFIG.get("path", "output_dir"))
        elif "bilibili.com" in url:
            return VideoType.BILIBILI, BiliDownloader(CONFIG.get("path", "output_dir"))
        else:
            return None
    video_type  = classify_video_type()[0]
    video_downloader = classify_video_type()[1]
    write_debug_log("Classified video type as " + video_type.name)
    archiver_api = ArchiveAPI()
    if mode != 1 and archiver_api.video_is_archived(video_downloader._get_video_id(url)):
        write_debug_log("Video is already archived. Skipping...")
        return False
    file_ext, file_size = video_downloader.download_video(url)
    video_downloader.download_thumbnail(url)
    video_metadata_dict = video_downloader.download_metadata(url)
    update_database(video_metadata_dict, video_type, file_ext, file_size)
    video_downloader.download_captions(url)
    return True

def delete_archived_video(video_id: str):
    """
    Deletes an archived video from the archive
    :param video_id: str
    """
    print(f"Deleting video {video_id} from archive...")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} delete "{CONFIG.get("path","rclone_video_target")}/{video_id}.webm"', shell=True)
    print(f"Deleting thumbnail {video_id} from archive...")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} delete "{CONFIG.get("path","rclone_thumbnail_target")}/{video_id}.jpg"', shell=True)
    print(f"Deleting metadata {video_id} from archive...")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} delete "{CONFIG.get("path","rclone_metadata_target")}/{video_id}.info.json"', shell=True)
    print(f"Deleting captions {video_id} from archive...")
    subprocess.run(f'{CONFIG.get("path","rclone_path")} delete "{CONFIG.get("path","rclone_captions_target")}/{video_id}"', shell=True)

def execute_server_worker(url: str, mode: int = 0):
    """
    To be executed through server.py when deploying an automatic archival
    :param url: str
    :param mode: int - 0 for normal archival, 1 for force archival
    """
    try:
        if mode == 2:
            delete_archived_video(url)
            discord_webhook.send_completed_message(CONFIG.get("discord", "webhook"), url, "Video deleted from archive.")
            return
        archive_result = archive_video(url, mode)
        if archive_result is False:
            return
        rclone_to_cloud()
        discord_webhook.send_completed_message(CONFIG.get("discord", "webhook"), url)
    except Exception as e:
        write_debug_log(f"Error encountered: {e}")
        discord_webhook.send_completed_message(CONFIG.get("discord", "webhook"), url, f"An error occurred while archiving the following video:\n\n{url}\n\nError: {e}")

# This function should only be manually called when you want to generate
# all channel images again
def update_all_channels(override: bool = False):
    import csv
    hostname = CONFIG.get("database", "host")
    user = CONFIG.get("database", "user")
    password = CONFIG.get("database", "password")
    database = CONFIG.get("database", "database")
    katsu = cutlet.Cutlet()
    server = SQLHandler(hostname, user, password, database)
    failed_file = open('failed_channels.csv', 'w')
    with open('channels_patchwork.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            channel_id = row[0]
            channel_name = row[1]
            print(f"Processing channel {channel_id}...")
            if server.check_row_exists("channels", "channel_id", channel_id) and not override:
                write_debug_log(f"Channel {channel_id} already exists in database. Skipping...")
                continue
            try:
                channel_data = channel_meta_archiver.download_youtube_banner_pfp_desc(channel_id, CONFIG.get("youtube", "api_key"))
                romanized_name = katsu.romaji(channel_data.name)
                server.insert_row("channels", "channel_id, channel_name, romanized_name, description", (channel_id, channel_data.name, romanized_name, channel_data.description))
                rclone_channel_images_to_cloud(channel_data.pfp, channel_data.banner)
            except Exception as e:
                print(f"Error encountered: {e}")
                failed_file.write(f"{channel_id},{channel_name}\n")


if __name__ == "__main__":
    # TODO: add commandline arguments support
    print("This script is not meant to be run directly. Please run server.py instead.")
