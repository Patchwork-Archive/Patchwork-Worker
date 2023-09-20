# Patchwork-Worker
Script for archiving videos from YouTube and directly upload to a S3 compatible storage through rclone.

Running through `worker.py` as `__main__` will download all videos from download_list.txt and upload them to the S3 compatible storage.

`server.py` is the worker mode where the program will fetch the next queue from the server and download the video and upload it to the S3 compatible storage. This process will repeat until execution is stopped.
