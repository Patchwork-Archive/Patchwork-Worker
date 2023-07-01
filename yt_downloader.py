import subprocess
import os
from tqdm import tqdm
import requests
from archive_api import ArchiveAPI
import thumbnail_downloader

MAXIMUM_FILE_SIZE_BYTES = 500000000  # 500 MB. Extra check here to make sure we don't download a file that is too big


class YouTubeDownloader:
    def __init__(
        self,
        download_list_file: str,
        output_dir,
        log_skip_file: str = "logs/skipped.txt",
        log_deleted_file: str = "logs/deleted.txt",
    ):
        self._LOG_SKIP_FILE = log_skip_file
        self._LOG_DELETED_FILE = log_deleted_file
        self._download_list_file = download_list_file
        self._output_dir = output_dir

    @staticmethod
    def get_yt_playlist_urls(playlist_url: str):
        api_url = f"https://cable.ayra.ch/ytdl/playlist.php?url={playlist_url}&API=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        print("Read playlist as: \n" + response.text)
        return response.text.split("\n")

    def _make_files_and_directories(self):
        """
        Makes the necessary files and directories for the downloader to work.
        """
        if not os.path.exists(self._LOG_SKIP_FILE):
            os.makedirs(os.path.dirname(self._LOG_SKIP_FILE))
            with open(self._LOG_SKIP_FILE, "w") as f:
                f.write("")
        with open(self._LOG_DELETED_FILE, "w") as f:
            f.write("")
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)

    def download_urls(self):
        archive_api = ArchiveAPI()
        url = "https://www.youtube.com/watch?v="
        self._make_files_and_directories()

        def _extract_video_id_from_url(url: str):
            """
            Gets the video id from a YouTube URL given youtu.be or youtube.com/watch?=
            """
            if "youtube.com/watch?v=" in url:
                return url.split("youtube.com/watch?v=")[1]
            elif "youtu.be/" in url:
                return url.split("youtu.be/")[1]
            elif "https://youtube.com/shorts/" in url:
                return url.split("https://youtube.com/shorts/")[1].replace(
                    "?feature=share", ""
                )

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

        def _download_urls_txt():
            """
            Download urls from a txt file, assumes one url per line
            """
            with open(self._download_list_file, "r", encoding="utf-8") as f:
                num_rows = sum(1 for _ in f)
                f.seek(0)
                for row in tqdm(f, total=num_rows):
                    if "playlist?list=" in row:
                        for url in self.get_yt_playlist_urls(row.strip()):
                            if archive_api.video_is_archived(_extract_video_id_from_url(url)):
                                print(url, "is already archived. Skipping.")
                                continue
                            _download_youtube_url(_extract_video_id_from_url(url))
                            thumbnail_downloader.download_thumbnail(_extract_video_id_from_url(url))
                    if archive_api.video_is_archived(_extract_video_id_from_url(row.strip())):
                        print(url, "is already archived. Skipping.")
                        continue
                    _download_youtube_url(_extract_video_id_from_url(row.strip()))
                    thumbnail_downloader.download_thumbnail(_extract_video_id_from_url(row.strip()))

        _download_urls_txt()
