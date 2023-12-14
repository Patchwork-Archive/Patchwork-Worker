from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
import argparse
import requests
import json
import requests

HOLODEX_API_KEY = ""
WORKER_AUTH = ""

def scrape_holodex_songs_and_covers(pages: int=1) -> list:
    """
    Uses selenium to scrape the Holodex search page for covers.
    :param: pages - number of pages to search through (from most recent)
    """
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    videos = []
    for i in range(pages):
        url = "https://holodex.net/search?q=type,value,text%0Atopic,Music_Cover,Music_Cover%0Atopic,Original_Song,Original_Song&page="+str(i)
        driver.get(url + str(pages))
        time.sleep(5)
        html_text = driver.page_source
        video_ids = re.findall(r'href="/watch/(\w+)"', html_text)
        video_ids = list(set(video_ids))
        videos = videos + video_ids
    return videos

def check_if_video_valid(videoID: str) -> bool:
    url = f"https://holodex.net/api/v2/videos/{videoID}"
    headers = {
        "X-APIKEY": ""
    }
    api_data = json.loads(requests.get(url, headers=headers).text)
    if api_data["status"] != "past":
        return False
    return 65 < api_data["duration"] < 480
    
def queue_video(videoID: str) -> bool:
    queueAPI = "https://archive.pinapelz.moe/api/worker/queue"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-AUTHENTICATION': ''
    }
    data = {
        'url': videoID,
        'mode': 0
    }
    response = requests.post(queueAPI, headers=headers, data=data)
    return response.status_code == 200
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Patchwork-Scraper',
                    description='A tool to help with scraping cover data for Patchwork Archive (primarily Holodex)',
                    )
    args = parser.parse_args()
    videos = [video for video in scrape_holodex_songs_and_covers(6) if check_if_video_valid(video)]
    for video in videos:
        if queue_video("https://youtube.com/watch?v="+video) :
            print("Successfully Queued " + video)
        else:
            print("Failed: " + video)

    

