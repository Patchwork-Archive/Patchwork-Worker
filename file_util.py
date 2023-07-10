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
    for file in os.listdir(file_path):
        os.remove(os.path.join(file_path, file))
