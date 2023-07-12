# import abstract class
from abc import ABC, abstractmethod
import os

class VideoDownloader(ABC):
    def __init__(
        self,
        output_dir: str,
        log_skip_file: str = "logs/skipped.txt",
        log_deleted_file: str = "logs/deleted.txt",
    ):
        self._LOG_SKIP_FILE = log_skip_file
        self._LOG_DELETED_FILE = log_deleted_file
        self._output_dir = output_dir
    
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
    
    @abstractmethod
    def download_urls(self):
        pass
    

