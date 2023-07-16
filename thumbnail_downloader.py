import urllib.request
import os
from tqdm import tqdm
import subprocess

RAGTAG_DRIVEBASES = [
    "0ALv7Nd0fL72dUk9PVA",
    "0AKRj4mXCkOw1Uk9PVA",
    "0AAVHoXgF39eKUk9PVA",
    "0ABbPCVFfmTmDUk9PVA",
    "0AO49onHihFmaUk9PVA",
    "0APcbUqyfMhbLUk9PVA",
    "0ANsY3BPG5rJwUk9PVA",
    "1ujQwfkOSa8_3Im-DSuAGp-oOfsTgj9u3",
    "1LvMYR3gmXPLzseeMnaMCW40Z1aKT3RJi",
    "1icHsiMjYCoBs1PeRV0zimhcEfBgy-OMM",

]

def download_thumbnail_yt(video_id: str):
    """
    1. Try to download from youtube
    2, If it fails try to download from ragtag
    4. If fail return False
    """
    if not os.path.exists("thumbnails"):
        os.makedirs("thumbnails")
    try:
        url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        urllib.request.urlretrieve(url, f"thumbnails/{video_id}.jpg")
        print("Successfully downloaded thumbnail from YouTube")
        return True
    except Exception:
        print("Error downloading thumbnail from youtube", video_id)
    try:
        url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
        urllib.request.urlretrieve(url, f"thumbnails/{video_id}.jpg")
        print("Successfully downloaded thumbnail from YouTube")
        return True
    except Exception:
        print("Error downloading thumbnail from youtube", video_id)
    for drivebase in RAGTAG_DRIVEBASES:
        url = f"https://content.archive.ragtag.moe/gd:{drivebase}/{video_id}/{video_id}.jpg"
        try:
            urllib.request.urlretrieve(url, f"thumbnails/{video_id}.jpg")
            print("Successfully downloaded from Ragtag Drivebase", drivebase)
            return True
        except Exception:
            print("Failed to download from Ragtag Drivebase:", drivebase)
    if not os.path.exists("error_thumb.txt"):
        open("error_thumb.txt", "w", encoding="utf-8").close()
    with open("error_thumb.txt", "a", encoding="utf-8") as error_thumb_file:
        print("Failed to download thumbnail:", video_id)
        error_thumb_file.write(video_id + "\n")
    return False

def fix_all_metadata(need_fixing):
    
    with open ("error_metadata.txt", "w", encoding="utf-8") as error_metadata_file:
        error_metadata_file.write("")
    for video_id in tqdm(need_fixing):
        fail = True
        if video_id.startswith("BV"):
            url = f"https://www.bilibili.com/video/{video_id}"
        else:
            url = f"https://www.youtube.com/watch?v={video_id}"
        subprocess.run(
        f'yt-dlp --write-info-json -o "metadata_output/%(id)s" --skip-download {url}',
        shell=True,
        # if video_id.info.json doesn't exist then keep going
    )
        if os.path.exists(f"metadata_output/{video_id}.info.json"):
            continue
        # try ragtag: https://content.archive.ragtag.moe/gd:{drive_base}/video_id/video_id.info.json
        for drive_base in RAGTAG_DRIVEBASES:
            url = f"https://content.archive.ragtag.moe/gd:{drive_base}/{video_id}/{video_id}.info.json"
            try:
                urllib.request.urlretrieve(url, f"metadata_output/{video_id}.info.json")
                print("Successfully downloaded from Ragtag Drivebase", drive_base)
                break
            except Exception:
                print("Failed to download from Ragtag Drivebase:", drive_base)
        if os.path.exists(f"metadata_output/{video_id}.info.json"):
            continue
        with open("error_metadata.txt", "a", encoding="utf-8") as error_metadata_file:
            print("Failed to download metadata:", video_id)
            error_metadata_file.write(video_id + "\n")


if __name__ == "__main__":
    with open("/rootVideo-Archive-Worker/needfixing.txt", "r", encoding="utf-8") as needfixing_file:
        need_fixing = needfixing_file.read().splitlines()
        fix_all_metadata(need_fixing=need_fixing)

