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
        headers = {'X-AUTHENTICATION': password}
        next_video = requests.get(f"{base_url}/api/worker/next", headers=headers)
        if next_video.status_code == 200:
            print(next_video.text)
            worker.execute_server_worker(next_video.text)
        elif next_video.status_code == 401:
            print("Invalid credentials. The password may be incorrect")
            time.sleep(500)
        else:
            print("No videos to archive at this time. Cooling down...")
            time.sleep(250)
        
        


if __name__ == '__main__':
    main()
