import json
import os

import boto3

from src.shared.driver import Driver
from src.shared.exceptions import VimeoUploaderInternalServerError, VimeoUploaderInvalidVideoIdError
from src.shared.model import VideoMetadata, VideoProcessResult


def handle_get_video_metadata(event, context):
    driver = Driver()
    platform = event['queryStringParameters']['platform']
    video_id = event['queryStringParameters']['video_id']
    try:
        video_metadata = driver.get_video_metadata(platform, video_id)
        print(f"Retrieved the video metadata for video id {video_id}")
        return {
            'statusCode': 200,
            'body': json.dumps(video_metadata, cls=CustomEncoder)
        }
    except VimeoUploaderInvalidVideoIdError:
        return {
            'statusCode': 404,
            'errorMessage': f"Failed to get metadata with video id {video_id} because it is invalid"
        }
    except VimeoUploaderInternalServerError:
        return {
            'statusCode': 500,
            'errorMessage': f"Failed to get metadata with video id {video_id} due to some internal server error"}


def handle_process_video_upload(event, context):
    driver = Driver(
        s3_client=boto3.client('s3'),
        environment=os.environ['ENV'])
    download_platform = event['download_platform']
    upload_platform = event['upload_platform']
    video_id = event['video_id']
    start_time_in_sec = event['start_time_in_sec']
    end_time_in_sec = event['end_time_in_sec']
    image_content = event['image_content']
    image_name = event['image_name']
    resolution = event['resolution']
    title = event['title']
    download = bool(event['download'])
    try:
        video_process_result = driver.process_video(
            download_platform,
            upload_platform,
            video_id,
            start_time_in_sec,
            end_time_in_sec,
            image_content,
            image_name,
            resolution,
            title,
            download)
        return {
            'statusCode': 200,
            'body': json.dumps(video_process_result, cls=CustomEncoder)
        }
    except VimeoUploaderInternalServerError:
        return {
            'statusCode': 500,
            'errorMessage': f"Failed to process the video with id {video_id} due to some internal server error"}


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, VideoMetadata):
            return obj.__dict__
        if isinstance(obj, VideoProcessResult):
            return obj.__dict__
        else:
            return super().default(obj)
