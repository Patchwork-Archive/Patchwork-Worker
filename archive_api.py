import urllib.request
import json

class ArchiveAPI:
    def __init__(self, base_url: str = "https://archive.pinapelz.moe/api/") -> None:
        if base_url[-1] != "/":
            base_url += "/"
        self.base_url = base_url
    
    def video_is_archived(self, video_id: str):
        """
        Checks if a video is archived on a specific archive instance
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        req = urllib.request.Request(self.base_url + "video/" + video_id, headers=headers)
        try:
            data = urllib.request.urlopen(req, timeout=10).read()
        except urllib.error.URLError as e:
            print(e)
            print(f"Unable to connect to server to check. Assuming video is not archived")
            return False
        json_data = json.loads(data)
        if "error" in json_data:
            return False
        return True

if __name__ == "__main__":
    api = ArchiveAPI()
    print(api.video_is_archived("0tpgZOv0i7U"))
    