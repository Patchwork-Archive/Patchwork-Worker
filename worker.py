import data_converter
from yt_downloader import YouTubeDownloader
import subprocess
import file_util
from input_enums import Options
from sql.sql_handler import SQLHandler
from tqdm import tqdm
import discord_webhook

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


def additional_commands_input():
    print("\n\n")
    print("Finished Task... What would you like to do next?")
    print("5. Download and Upload again")
    print("6. Remove duplicates from ndjson")
    print("7. Add data to DB")
    print("99. Exit")
    print("\n\n")
    try:
        return int(input())
    except ValueError:
        print("Invalid Input")
        return additional_commands_input()


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
    nd_json_reader = file_util.NDJsonReader(CONFIG.get("path", "ndjson_path"))
    download_and_upload(confirmations=False)
    cmd = additional_commands_input()
    
    while cmd != Options.EXIT.value:
        match cmd:
            case Options.DOWNLOAD_AND_UPLOAD.value:
                download_and_upload()
            case Options.REMOVE_DUPLICATES.value:
                nd_json_reader.remove_duplicates()
            case Options.ADD_TO_DATABASE.value:
                update_database()
            case _:
                print("Invalid Input")
        cmd = additional_commands_input()


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
