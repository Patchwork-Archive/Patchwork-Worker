import configparser
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
    for item in os.listdir(file_path):
        item_path = os.path.join(file_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            try:
                os.rmdir(item_path)
            except OSError:
                print(f"Failed to remove folder: {item_path}. It might not be empty.")
        else:
            # If the item is neither a file nor a directory (e.g., a symbolic link), ignore it
            print(f"Ignoring item: {item_path}. It is neither a file nor a folder.")