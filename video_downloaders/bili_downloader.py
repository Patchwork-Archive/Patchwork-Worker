from video_downloaders.video_downloader import VideoDownloader
from archive_api import ArchiveAPI
import re
from tqdm import tqdm
import subprocess
import os

MAXIMUM_FILE_SIZE_BYTES = 500000000 

class BiliBiliDownloader(VideoDownloader):
        def __init__(
        self,
        output_dir: str,
        log_skip_file: str = "logs/skipped.txt",
        log_deleted_file: str = "logs/deleted.txt",
        ):
            super().__init__(output_dir, log_skip_file, log_deleted_file)
        
        def download_urls(self, video_url: str):
            archive_api = ArchiveAPI()
            url = "https://www.bilibili.com/video/"
            self._make_files_and_directories()

            def _extract_video_id_from_url(url: str):
                 video_id = re.search(r"(?<=\/video\/)[A-Za-z0-9]+", url).group()
                 return video_id
            

            def _download_bili_thumbnail():
                subprocess.run(f'yt-dlp {video_url} --write-thumbnail --no-download -o "thumbnails/%(id)s.%(ext)s"', shell=True)

            def _download_bili_url(video_id: str):
                output_path = os.path.join(self._output_dir, f"{video_id}")
                full_url = url + video_id
                if archive_api.video_is_archived(video_id):
                    print(full_url, "is already archived. Skipping.")
                    return
                print("Downloading", full_url)
                subprocess.run(
                    f'yt-dlp {full_url} -f "bestvideo[ext=mp4]+bestaudio" -o "{self._output_dir}/%(id)s.%(ext)s" --add-metadata',
                shell=True,
                )
                try:
                    if os.path.getsize(output_path) > MAXIMUM_FILE_SIZE_BYTES:
                        with open(self._LOG_SKIP_FILE, "a") as f:
                            f.write(f"{video_id}\n")
                        os.remove(output_path)
                except Exception as e:
                    with open(self._LOG_DELETED_FILE, "a") as f:
                        f.write(f"{video_id}  " + str(e) + "\n")
            

            def _download_url():
                """
                Download urls from a txt file, assumes one url per line
                """
                if "playlist?list=" in video_url:
                    for url in self.get_yt_playlist_urls(video_url.strip()):
                        if archive_api.video_is_archived(_extract_video_id_from_url(url)):
                            print(url, "is already archived. Skipping.")
                            return
                        _download_bili_url(_extract_video_id_from_url(url))
                        _download_bili_thumbnail()
                if archive_api.video_is_archived(_extract_video_id_from_url(video_url.strip())):
                    print(video_url.strip(), "is already archived. Skipping.")
                    return
                _download_bili_url(_extract_video_id_from_url(video_url.strip()))
                _download_bili_thumbnail()
            _download_url()
            
                 
            
                