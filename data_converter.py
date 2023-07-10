import os
import subprocess
import json
from tqdm import tqdm


def get_all_files_in_directory(directory: str, file_type: str = ""):
    """
    Get all files in a directory if file_type is empty str then find all files
    If not then only the extension. Makes a generator object
    """
    for file in os.listdir(directory):
        if file_type == "":
            yield file
        elif file.endswith(file_type):
            yield file


def convert_all_mkv_to_webm(directory: str):
    """
    Converts all mkv files in a directory to webm and then deletes the mkv
    """
    for file in get_all_files_in_directory(directory, ".mkv"):
        subprocess.run(
            f"ffmpeg -i {file} -c:v libvpx -crf 10 -c:a libvorbis {file.split('.')[0]}.webm"
        )
        os.remove(file)


def reformat_url(text: str):
    """
    Parses the url id from some text
    """
    return "https://www.youtube.com/watch?v=" + text.split(".")[:-1][0]


def download_video_data(url: str):
    def convert_description_to_single_line(description):
        return description.replace("\n", " \\n")

    subprocess.run(
        f"yt-dlp --write-info-json -o temp --skip-download {reformat_url(url)}",
        shell=True,
    )
    video_obj = json.loads(open("temp.info.json", "r", encoding="utf-8").read())
    vid_id = video_obj["id"]
    vid_title = video_obj["title"]
    uploader = video_obj["uploader"]
    vid_date = video_obj["upload_date"]
    channel_id = video_obj["channel_id"]
    channel_name = video_obj["channel"]
    description = convert_description_to_single_line(video_obj["description"])
    vid_date = f"{vid_date[:4]}-{vid_date[4:6]}-{vid_date[6:]}"
    try:
        os.remove("temp.info.json")
    except Exception:
        print("Error removing temp.info.json")
    json_obj = {
        "video_id": vid_id,
        "title": vid_title,
        "channel_id": channel_id,
        "uploader": uploader,
        "upload_date": vid_date,
        "description": description,
        "channel_name": channel_name,
    }
    return json.dumps(json_obj, ensure_ascii=False) + "\n"

def generate_database_row_data(video_input_dir: str, file_type:str):
    files = get_all_files_in_directory(video_input_dir, file_type)
    for file in tqdm(files, desc="Processing files", unit="file"):
        video_metadata = json.loads(download_video_data(file))
        yield video_metadata
