import data_converter
from yt_downloader import YouTubeDownloader
import subprocess
import file_util
from input_enums import Options
from datetime import datetime

CONFIG = file_util.read_config(
    "config.ini",
)


def rclone_to_cloud():
    subprocess.run(
        f'{CONFIG.get("path","rclone_path")} -P copy "{CONFIG.get("path","download_output_path")}" "{CONFIG.get("path","rclone_cloud_target")}"',
        shell=True,
    )


def additional_commands_input():
    print("\n\n")
    print("Finished Task... What would you like to do next?")
    print("1. Sort Videos ndjson")
    print("2. Commit to remote")
    print("3. Search for video in ndjson (must be sorted)")
    print("4. Validate ndjson")
    print("5. Download and Upload again")
    print("6. Exit")
    print("\n\n")
    try:
        return int(input())
    except ValueError:
        print("Invalid Input")
        return additional_commands_input()


def download_and_upload():
    print("Clear output folder? (y/n)")
    file_util.clear_output_folder(
        CONFIG.get("path", "download_output_path")
    ) if input() == "y" else print("Skipping...")
    print("Download Videos? (y/n)")
    downloader = YouTubeDownloader(
        "download_list.txt", CONFIG.get("path", "download_output_path")
    )
    if input() == "y":
        downloader.download_urls()
        data_converter.convert_all_mkv_to_webm(
            CONFIG.get("path", "download_output_path")
        )
    print("Download Complete... Ready to generate ndjson data (y/n)")
    data_converter.generate_json_data(
        video_input_dir=CONFIG.get("path", "download_output_path"),
        file_type=".webm",
        ndjson_path=CONFIG.get("path", "ndjson_path"),
    ) if input() == "y" else print("Skipping...")
    print("JSON Data Generated... Upload to Cloud? (y/n)")
    rclone_to_cloud() if input() == "y" else print("Skipping...")


def _make_commit_message():
    commit_message = f"Generation at {datetime.now()}\n\n"
    for video in data_converter.get_all_files_in_directory(
        CONFIG.get("path", "download_output_path"), file_type="webm"
    ):
        commit_message += f"{video}\n"
    return commit_message


def main():
    nd_json_reader = file_util.NDJsonReader(CONFIG.get("path", "ndjson_path"))
    download_and_upload()
    cmd = additional_commands_input()
    while cmd != Options.EXIT.value:
        match cmd:
            case Options.SORT_VIDEOS.value:
                nd_json_reader.sort_ndjson("video_id")
            case Options.COMMIT_TO_REMOTE.value:
                data_converter.commit_and_push(
                    CONFIG.get("path", "git_repo_path"), _make_commit_message()
                )
            case Options.SEARCH_FOR_VIDEO.value:
                print("Enter video id to search for: ")
                video_id = input()
                nd_json_reader.search_for_video_id(video_id)
            case Options.VALIDATE_NDJSON.value:
                nd_json_reader.validate_ndjson()
            case Options.DOWNLOAD_AND_UPLOAD.value:
                download_and_upload()
            case _:
                print("Invalid Input")
        cmd = additional_commands_input()


if __name__ == "__main__":
    main()
