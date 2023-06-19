import configparser
import json
from operator import itemgetter
import os


def read_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            yield line.strip()


def read_config(file_path: str):
    """
    Reads a config file and returns a dictionary of the config
    :param: file_path: str
    :return: dict
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    return config


def clear_output_folder(file_path: str):
    for file in os.listdir(file_path):
        os.remove(os.path.join(file_path, file))


class NDJsonReader:
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path

    def sort_ndjson(self, sort_key: str):
        """
        Sorts a ndjson by a given key
        """
        with open(self._file_path, "r", encoding="utf-8") as f:
            data = [json.loads(line) for line in f]
        sorted_data = sorted(data, key=itemgetter(sort_key))
        with open(self._file_path, "w", encoding="utf-8") as f:
            for item in sorted_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def search_for_video_id(self, video_id: str):
        """
        Binary search for a video id in a ndjson file
        """

        def binary_search():
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = [json.loads(line) for line in f]
            # sort the list by the video id
            sorted_data = sorted(data, key=lambda x: x["video_id"])
            # perform binary search to find the video id
            left = 0
            right = len(sorted_data) - 1
            while left <= right:
                mid = (left + right) // 2
                if sorted_data[mid]["video_id"] == video_id:
                    return sorted_data[mid]
                elif sorted_data[mid]["video_id"] < video_id:
                    left = mid + 1
                else:
                    right = mid - 1
            return None

        result = binary_search()
        if result is None:
            print("Video id not found")
        else:
            print(result)

    def validate_ndjson(self):
        """
        Validates a ndjson file
        """
        with open(self._file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    print("Invalid JSON")
                    return
        print("Valid JSON")
