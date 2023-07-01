import urllib.request
import os
from tqdm import tqdm

RAGTAG_DRIVEBASES = [
    "0ALv7Nd0fL72dUk9PVA",
    "0AKRj4mXCkOw1Uk9PVA",
    "0AAVHoXgF39eKUk9PVA",
    "0ABbPCVFfmTmDUk9PVA",
    "0AO49onHihFmaUk9PVA",
    "0APcbUqyfMhbLUk9PVA",
    "0ANsY3BPG5rJwUk9PVA",
]
def download_thumbnail(video_id: str):
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
        print("Successfully downloaded from YouTube")
        return True
    except Exception:
        print("Error downloading thumbnail from youtube", video_id)
    for drivebase in RAGTAG_DRIVEBASES:
        url = f"https://the-eye.eu/archive.ragtag.moe/{drivebase}/archive/{video_id}/{video_id}.jpg"
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


if __name__ == "__main__":
    with open("thumbnail_queue.txt", "r", encoding="utf-8") as download_queue_file:
        all_files = os.listdir("thumbnails")
        video_ids = download_queue_file.read().split("\n")
    for video_id in tqdm(video_ids, desc="Downloading Thumbnails", unit="thumbnail"):
        file_name = f"{video_id}.jpg"
        if file_name in all_files:
            print("Thumbnail already downloaded:", video_id)
            continue
        download_thumbnail(video_id)
