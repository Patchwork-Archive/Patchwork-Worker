# import abstract class
from abc import ABC, abstractmethod
import os
from datetime import datetime

class VideoDownloader(ABC):
    def __init__(
        self,
        output_dir: str,
        log_skip_file: str = "logs/skipped.txt",
        log_deleted_file: str = "logs/deleted.txt",
        max_file_size_bytes: int = 500000000,
    ):
        self._LOG_SKIP_FILE = log_skip_file
        self._LOG_DELETED_FILE = log_deleted_file
        self._output_dir = output_dir
        self._max_file_size_bytes = max_file_size_bytes
    
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
    
    def _write_to_log_skip(self, video_url: str):
        """
        Writes a video URL to the log_skip_file
        """
        with open(self._LOG_SKIP_FILE, "a") as f:
            f.write(f"{video_url}\n")
    
    def _write_to_log_deleted(self, video_url: str):
        """
        Writes a video URL to the log_deleted_file
        """
        with open(self._LOG_DELETED_FILE, "a") as f:
            f.write(f"{video_url}\n")
    
    def _write_debug_log(self, message: str):
        """
        Prints a debug message to the standard output with the class name and a timestamp
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
    @abstractmethod
    def download_video(self, video_url: str, file_type:str):
        """
        Downloads a video from a given URL to OUTPUT_DIR/video
        To be implemented by child classes
        """
        pass

    @abstractmethod
    def download_thumbnail(self, video_url: str):
        """
        Downloads a thumbnail from a given URL to OUTPUT_DIR/thumbnail
        To be implemented by child classes
        """
        pass

    @abstractmethod
    def download_captions(self):
        """
        Downloads all non-auto-generated captions from a given URL to OUTPUT_DIR/captions
        To be implemented by child classes
        """
        pass
    
    @abstractmethod
    def download_metadata(self, video_url: str):
        """
        Downloads metadata from a given URL to OUTPUT_DIR/metadata
        To be implemented by child classes
        """
        pass


    

