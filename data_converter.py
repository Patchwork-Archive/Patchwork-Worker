import os
import subprocess
import json


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
            f"ffmpeg -i {directory}/{file} -c:v libvpx -crf 10 -c:a libvorbis {directory}/{file.split('.')[0]}.webm"
        , shell=True)
        os.remove(directory+"/"+file)

def convert_all_mp4_to_webm(directory: str):
    """
    Converts all mp4 files in a directory to webm and then deletes the mp4
    """
    for file in get_all_files_in_directory(directory, ".mp4"):
        subprocess.run(
            f"ffmpeg -i {directory}/{file} {directory}/{file.split('.')[0]}.webm"
        , shell=True)
        os.remove(directory+"/"+file)


def download_video_data(url: str):
    def convert_description_to_single_line(description):
        return description.replace("\n", " \\n")
    
    subprocess.run(
        f"yt-dlp --write-info-json -o temp --skip-download {url}",
        shell=True,
    )
    video_obj = json.loads(open("temp.info.json", "r", encoding="utf-8").read())
    if "youtube" in url:
        vid_id = video_obj["id"]
        vid_title = video_obj["title"]
        uploader = video_obj["uploader"]
        vid_date = video_obj["upload_date"]
        channel_id = video_obj["channel_id"]
        channel_name = video_obj["channel"]
        description = convert_description_to_single_line(video_obj["description"])
    elif "bilibili" in url:
        vid_id = video_obj["id"]
        vid_title = video_obj["title"]
        uploader = video_obj["uploader"]
        vid_date = video_obj["upload_date"]
        channel_id = video_obj["uploader_id"]
        channel_name = video_obj["uploader"]
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

def generate_database_row_data(download_list_path: str):
    with open(download_list_path, "r", encoding="utf-8") as f:
        for line in f:
            video_metadata = json.loads(download_video_data(line))
            yield video_metadata

if __name__ == "__main__":
    print(download_video_data("https://www.bilibili.com/video/BV1Xe411M7Hw/"))