"""
Archives various information about a given channel.
"""

import requests
from collections import namedtuple

ChannelData = namedtuple("ChannelData", ["banner", "pfp", "name", "description"])

def download_youtube_banner_pfp_desc(channel_id: str, api_key: str ) -> ChannelData:
    """
    Downloads the banner and profile picture of a channel
    :param channel_id: str
    :param api_key: str
    """
    channel_data = requests.get(f"https://www.googleapis.com/youtube/v3/channels?part=brandingSettings,snippet&id={channel_id}&key={api_key}")
    channel_data = channel_data.json()
    channel_name = channel_data["items"][0]["snippet"]["title"]
    banner_url = channel_data["items"][0]["brandingSettings"]["image"]["bannerExternalUrl"]
    pfp_url = channel_data["items"][0]["snippet"]["thumbnails"]["default"]["url"]
    description = channel_data["items"][0]["snippet"]["description"]
    with open(f"{channel_id}_banner.jpg", "wb") as f:
        f.write(requests.get(banner_url).content)
    with open(f"{channel_id}_pfp.jpg", "wb") as f:
        f.write(requests.get(pfp_url).content)
    return ChannelData(f"{channel_id}_banner.jpg", f"{channel_id}_pfp.jpg", channel_name, description)
