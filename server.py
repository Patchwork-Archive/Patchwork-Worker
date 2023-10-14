import worker
import requests
import time
import configparser
import sys
import json

ERROR_WAIT_TIME = 500 # seconds
COOLDOWN_WAIT_TIME = 250 # seconds

def read_config(file_path: str):
    """
    Reads a config file and returns a dictionary of the config
    :param: file_path: str
    :return: dict
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def send_heartbeat(status: str):
    """
    Sends a heartbeat to the server
    :param: status: str
    """
    config = read_config("config.ini")
    base_url = config.get("queue", "base_url")
    password = config.get("queue", "worker_password")
    name = config.get("queue", "worker_name")
    headers = {'X-AUTHENTICATION': password}
    requests.post(f"{base_url}/api/worker/heartbeat", headers=headers, data={"status": status, "name": name})


def wait_and_check_for_quit(seconds: int):
    try:
        for _ in range(seconds):
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Sending offline heartbeat...")
        send_heartbeat("Offline")
        exit()


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--offline_msg":
            send_heartbeat(sys.argv[2])
            exit()
    config = read_config("config.ini")
    base_url = config.get("queue", "base_url")
    password = config.get("queue", "worker_password")
    send_heartbeat("Offline")
    try:
        while True:
            headers = {'X-AUTHENTICATION': password}
            next_video = requests.get(f"{base_url}/api/worker/next", headers=headers)
            if next_video.status_code == 200:
                print("Found video to archive. Starting...")
                next_video_data = json.loads(next_video.text)
                send_heartbeat("Archiving " + next_video_data["next_video"])
                mode = next_video_data["mode"]
                worker.execute_server_worker(next_video_data["next_video"], mode)
            elif next_video.status_code == 401:
                print("Invalid credentials. The password may be incorrect")
                send_heartbeat("Invalid credentials. The password may be incorrect")
                wait_and_check_for_quit(ERROR_WAIT_TIME)
            else:
                print("No videos to archive at this time. Cooling down...")
                send_heartbeat("Idle. Waiting for work...")
                wait_and_check_for_quit(COOLDOWN_WAIT_TIME)
    except Exception as e:
        if str(e) == "KeyboardInterrupt":
            print("Keyboard interrupt detected. Sending offline heartbeat...")
            send_heartbeat("Offline")
        else:
            print("An error occurred. Sending offline heartbeat...")
            send_heartbeat("Offline - An error occured " + str(e))
            print(e)
            
        


if __name__ == '__main__':
    main()
