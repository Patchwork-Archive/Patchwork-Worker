import subprocess
from tqdm import tqdm
import requests
from archive_api import ArchiveAPI
import thumbnail_downloader
from video_downloaders.video_downloader import VideoDownloader
import os
import re

MAXIMUM_FILE_SIZE_BYTES = 500000000  # 500 MB. Extra check here to make sure we don't download a file that is too big


class YouTubeDownloader(VideoDownloader):
    def __init__(
        self,
        output_dir: str,
        log_skip_file: str = "logs/skipped.txt",
        log_deleted_file: str = "logs/deleted.txt",
    ):
        super().__init__(output_dir, log_skip_file, log_deleted_file)

    @staticmethod
    def get_yt_playlist_urls(playlist_url: str):
        api_url = f"https://cable.ayra.ch/ytdl/playlist.php?url={playlist_url}&API=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        print("Read playlist as: \n" + response.text)
        return response.text.split("\n")

    def download_urls(self, video_url: str):
        archive_api = ArchiveAPI()
        url = "https://www.youtube.com/watch?v="
        self._make_files_and_directories()

        def _extract_video_id_from_url(url: str):
            """
            Gets the video id from a YouTube URL given youtu.be or youtube.com/watch?=
            """
            pattern = r"(?:youtube\.com/watch\?v=|youtu\.be/|https://youtube\.com/shorts/|https://www.youtube\.com/shorts/)([\w-]+)"
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            return None

        def _download_youtube_url(url_id: str):
            output_path = os.path.join(self._output_dir, f"{url_id}")
            print(
                "Executing",
                f'yt-dlp {url}{url_id} -f "bestvideo[height<=1080][ext=webm]+bestaudio" -o "{self._output_dir}/%(id)s.%(ext)s" --add-metadata',
            )
            subprocess.run(
                f'yt-dlp {url}{url_id} -f "bestvideo[height<=1080][ext=webm]+bestaudio" -o "{self._output_dir}/%(id)s.%(ext)s" --add-metadata',
                shell=True,
            )
            try:
                if os.path.getsize(output_path) > MAXIMUM_FILE_SIZE_BYTES:
                    with open(self._LOG_SKIP_FILE, "a") as f:
                        f.write(f"{url_id}\n")
                    os.remove(output_path)
            except Exception as e:
                with open(self._LOG_DELETED_FILE, "a") as f:
                    f.write(f"{url_id}  " + str(e) + "\n")

        def _download_url():
            """
            Download urls from a txt file, assumes one url per line
            """
            if "playlist?list=" in video_url:
                for url in self.get_yt_playlist_urls(video_url.strip()):
                    if archive_api.video_is_archived(_extract_video_id_from_url(url)):
                        print(url, "is already archived. Skipping.")
                        return
                    _download_youtube_url(_extract_video_id_from_url(url))
                    thumbnail_downloader.download_thumbnail_yt(_extract_video_id_from_url(url))
            if archive_api.video_is_archived(_extract_video_id_from_url(video_url.strip())):
                print(video_url.strip(), "is already archived. Skipping.")
                return
            _download_youtube_url(_extract_video_id_from_url(video_url.strip()))
            thumbnail_downloader.download_thumbnail_yt(_extract_video_id_from_url(video_url.strip()))

        _download_url()

