import worker
import requests
import time
import configparser

def read_config(file_path: str):
    """
    Reads a config file and returns a dictionary of the config
    :param: file_path: str
    :return: dict
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    return config


def main():
    config = read_config("config.ini")
    base_url = config.get("queue", "base_url")
    password = config.get("queue", "worker_password")
    while True:
        next_video = requests.get(f"{base_url}/api/worker/next?password={password}")
        if next_video.status_code == 200:
            print(next_video.text)
            worker.execute_server_worker(next_video.text)
        else:
            print("No videos to archive at this time.")
        print("Cooldown until next check")
        time.sleep(300)


if __name__ == '__main__':
    main()
