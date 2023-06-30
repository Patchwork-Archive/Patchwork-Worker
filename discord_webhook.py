import requests
import json

def send_completed_message(webhook_url: str, urls: list):
    if webhook_url == "":
        print("No Discord webhook URL provided. Skipping...")
        return
    urls = "\n".join(urls)
    message = f"The Following Videos Have Been Archived\n\n{urls}"
    payload = {
        "content": message,
    }
    payload_json = json.dumps(payload)
    response = requests.post(webhook_url, data=payload_json, headers={"Content-Type": "application/json"})
    if response.status_code != 204:
        print(f"Failed to send message to Discord webhook: {response.text}")