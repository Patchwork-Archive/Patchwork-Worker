import subprocess
from video_downloaders.video_downloader import VideoDownloader
import os
import re
import json

class BiliDownloader(VideoDownloader):
    """
    A class that downloads Bilibili videos using youtube-dl
    """
    def __init__(
        self,
        output_dir: str,
        log_skip_file: str = "logs/skipped.txt",
        log_deleted_file: str = "logs/deleted.txt",
        cookies_file: str = "bilicookies.txt"
    ):
        """
        Creates a new BiliDownloader object
        :param output_dir: str - The directory to output the downloaded videos to
        :param log_skip_file: str - The file to log skipped videos to
        :param log_deleted_file: str - The file to log deleted videos to
        """
        super().__init__(output_dir, log_skip_file, log_deleted_file)
        self._cookies_file = cookies_file

    def _get_video_id(self, video_url: str) -> str:
        """
        Tries multiple methods to get the video ID from a YouTube URL
        Also works to get the playlist ID from a YouTube playlist URL
        :param video_url: str
        :return: str
        """
        if "bilibili.com" in video_url:
            match_result = re.search("https:\/\/www\.bilibili\.com\/video\/(BV[0-9A-Za-z]+)", video_url)
            return match_result.group(1)
        

    def download_video(self, video_url: str, file_type:str="mp4"):
        self._write_debug_log(f"Downloading video using yt-dlp {video_url}")
        subprocess.run(
            f'yt-dlp "{video_url}" -f "bestvideo+bestaudio" -o "{self._output_dir}/video/%(id)s.%(ext)s" --add-metadata --cookies cookies.txt',
            shell=True,
        )
        if os.path.getsize(f"{self._output_dir}/video/{self._get_video_id(video_url)}.mp4") > self._max_file_size_bytes:
            self._write_debug_log(f"Video {video_url} exceeds max file size. Deleting...")
            self._write_to_log_deleted(video_url)
            os.remove(f"{self._output_dir}/video/{self._get_video_id(video_url)}.mp4")
            return

    def download_thumbnail(self, video_url: str):
        self._write_debug_log(f"Downloading thumbnail using yt-dlp {video_url}")
        subprocess.run(
            f'yt-dlp "{video_url}" --write-thumbnail --skip-download --convert-thumbnails jpg -o "{self._output_dir}/thumbnail/%(id)s.%(ext)s" --cookies cookies.txt',
            shell=True,
        )

    def download_metadata(self, video_url: str) -> dict:
        """
        Metadata considered as .info.json file
        Returns a dictionary of certain key-value pairs for backup DB
        """
        def format_description_escape_char(description):
            """
            Formats the description newlines to escape characters
            """
            return description.replace("\n", " \\n")
        
        self._write_debug_log(f"Downloading metadata (.info.json) using yt-dlp {video_url}")
        subprocess.run(
            f'yt-dlp --write-info-json -o "output/metadata/%(id)s.%(ext)s" --skip-download {video_url} --cookies cookies.txt',
            shell=True,
        )
        video_obj = json.loads(open(f"output/metadata/{self._get_video_id(video_url)}.info.json", "r", encoding="utf-8").read())
        description = format_description_escape_char(video_obj["description"])
        vid_date = video_obj["upload_date"]
        vid_date = f"{vid_date[:4]}-{vid_date[4:6]}-{vid_date[6:]}"
        return {
            "video_id": video_obj["id"],
            "title": video_obj["title"],
            "channel_id": video_obj["uploader_id"],
            "uploader": video_obj["uploader"],
            "upload_date": vid_date,
            "description": description,
            "channel_name": video_obj["uploader"],
        }

    def download_captions(self, video_url: str):
        print("[BiliDownloader] Captions currently not supported for Bilibili videos")
        if not os.path.exists(f"{self._output_dir}/captions/{self._get_video_id(video_url)}"):
            os.makedirs(f"{self._output_dir}/captions/{self._get_video_id(video_url)}")
        pass

