import requests
import json

def send_completed_message(webhook_url: str, url: str, message: str = "The following video has been archived\n\n"):
    """
    Optionally sends a message to a Discord webhook when a video has been archived
    Used for notification purposes/broadcasting
    """
    if webhook_url == "":
        print("No Discord webhook URL provided. Skipping...")
        return
    message_text = f"{message}{url}"
    payload = {
        "content": message_text,
    }
    payload_json = json.dumps(payload)
    response = requests.post(webhook_url, data=payload_json, headers={"Content-Type": "application/json"})
    if response.status_code != 204:
        print(f"Failed to send message to Discord webhook: {response.text}")