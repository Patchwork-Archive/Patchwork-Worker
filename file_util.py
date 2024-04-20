import configparser
import os

def read_config(file_path: str):
    """
    Reads a config file and returns a dictionary of the config
    :param: file_path: str
    :return: dict
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    return config
