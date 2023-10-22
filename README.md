# Patchwork-Worker
Script for archiving videos from YouTube and directly upload to a S3 compatible storage through rclone.

# Deploying
After configuring `config.ini` and running `server.py`, the worker will send it's heartbeat (status) to the backend server every 2 minutes. During the same loop it will also check to see if there are any videos in the queue, if so then it will begin archive them.
