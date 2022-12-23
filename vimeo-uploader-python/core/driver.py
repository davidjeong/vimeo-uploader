import logging
import webbrowser
from typing import Optional

import requests
from google.protobuf.json_format import ParseDict

from generated import model_pb2

logging.basicConfig(
    filename='output.log',
    encoding='utf-8',
    level=logging.INFO)

APP_DIRECTORY_NAME = "Vimeo Uploader"
REQUEST_HEADERS = {"Content-Type": "application/json"}


class Driver:
    """
    Driver for the video/audio interaction
    """

    def __init__(self, aws_api_gateway_url: str, process_video_function_url) -> None:
        """
        Initialize the driver used to interact with video/audio resources
        """
        self.aws_api_gateway_url = aws_api_gateway_url
        self.process_video_function_url = process_video_function_url

    def get_video_metadata(
            self,
            platform: str,
            video_id: str) -> Optional[model_pb2.VideoMetadata]:
        try:
            response = requests.get(
                url=f"{self.aws_api_gateway_url}/video-metadata",
                params={
                    "platform": platform,
                    "video_id": video_id
                },
                headers=REQUEST_HEADERS
            )
            if response.status_code == 200:
                video_metadata = ParseDict(
                    response.json(), model_pb2.VideoMetadata())
                return video_metadata
            elif response.status_code == 404:
                logging.info(f"Video with id {video_id} is not available")
                return None
        except requests.exceptions.RequestException as e:
            logging.error("Failed to get request with exception %s", e)
            return None

    def process(
            self,
            download_platform: str,
            upload_platform: str,
            video_id: str,
            start_time_in_sec: int,
            end_time_in_sec: int,
            image_content: str,
            image_name: str,
            resolution: str,
            title: str,
            download: bool) -> None:
        try:
            response = requests.post(
                url=self.process_video_function_url,
                json={
                    "download_platform": download_platform,
                    "upload_platform": upload_platform,
                    "video_id": video_id,
                    "start_time_in_sec": start_time_in_sec,
                    "end_time_in_sec": end_time_in_sec,
                    "image_content": image_content,
                    "image_name": image_name,
                    "resolution": resolution,
                    "title": title,
                    "download": download
                },
                headers=REQUEST_HEADERS
            )
            if response.status_code == 200:
                video_process_result = ParseDict(
                    response.json(), model_pb2.VideoProcessResult()
                )
            elif response.status_code == 500:
                logging.error(f"Video with id {video_id} failed to process")

        except requests.exceptions.RequestException as e:
            logging.error("Failed to get request with exception %s", e)
            return None

        # Open the url in browser, if possible
        if video_process_result.upload_url:
            webbrowser.open_new(video_process_result.upload_url)
