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

def main():
    config = read_config("config.ini")
    base_url = config.get("queue", "base_url")
    password = config.get("queue", "worker_password")
    send_heartbeat("Online")
    try:
        while True:
            headers = {'X-AUTHENTICATION': password}
            next_video = requests.get(f"{base_url}/api/worker/next", headers=headers)
            if next_video.status_code == 200:
                print("Found video to archive. Starting...")
                send_heartbeat("Archiving " + next_video.text)
                worker.execute_server_worker(next_video.text)
            elif next_video.status_code == 401:
                print("Invalid credentials. The password may be incorrect")
                time.sleep(500)
            else:
                print("No videos to archive at this time. Cooling down...")
                send_heartbeat("Idle. Waiting for work...")
                time.sleep(250)
    except Exception as e:
        if str(e) == "KeyboardInterrupt":
            print("Keyboard interrupt detected. Sending offline heartbeat...")
            send_heartbeat("Offline")
        else:
            print("An error occurred. Sending offline heartbeat...")
            send_heartbeat("Offline - An error occured " + str(e))
            
        


if __name__ == '__main__':
    main()
