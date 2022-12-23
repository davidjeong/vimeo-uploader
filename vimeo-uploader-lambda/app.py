import os

import boto3
from botocore.client import BaseClient
from google.protobuf.json_format import MessageToJson

from core.driver import Driver, get_streaming_platform
from core.exceptions import VimeoUploaderInternalServerError, VimeoUploaderInvalidVideoIdError
from core.streaming_platform import StreamingPlatform


def handle_get_video_metadata(event, context):
    platform = event['queryStringParameters']['platform']
    video_id = event['queryStringParameters']['video_id']
    return _handle_get_video_metadata(
        get_streaming_platform(platform), video_id)


def _handle_get_video_metadata(
        download_platform: StreamingPlatform,
        video_id: str):
    driver = Driver(download_platform=download_platform)
    try:
        video_metadata = driver.get_video_metadata(video_id)
        print(f"Retrieved the video metadata for video id {video_id}")
        return {
            'headers': {
                'Content-Type': 'application/json'
            },
            'statusCode': 200,
            'body': MessageToJson(video_metadata)
        }
    except VimeoUploaderInvalidVideoIdError:
        return {
            'headers': {
                'Content-Type': 'application/json'
            },
            'statusCode': 404,
            'errorMessage': f"Failed to get metadata with video id {video_id} because it is invalid"
        }
    except VimeoUploaderInternalServerError:
        return {
            'headers': {
                'Content-Type': 'text/plain'
            },
            'statusCode': 500,
            'errorMessage': f"Failed to get metadata with video id {video_id} due to some internal server error"}


def handle_process_video_upload(event, context):
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
    s3_client = boto3.client('s3')
    return _handle_process_video_upload(
        s3_client,
        get_streaming_platform(download_platform),
        get_streaming_platform(upload_platform),
        video_id,
        start_time_in_sec,
        end_time_in_sec,
        image_content,
        image_name,
        resolution,
        title,
        download)


def _handle_process_video_upload(
        s3_client: BaseClient,
        download_platform: StreamingPlatform,
        upload_platform: StreamingPlatform,
        video_id: str,
        start_time_in_sec: int,
        end_time_in_sec: int,
        image_content: bytes,
        image_name: str,
        resolution: str,
        title: str,
        download: bool):
    driver = Driver(s3_client, download_platform, upload_platform)
    try:
        video_process_result = driver.process_video(
            video_id,
            start_time_in_sec,
            end_time_in_sec,
            image_content,
            image_name,
            resolution,
            title,
            download)
        return {
            'headers': {
                'Content-Type': 'application/json'
            },
            'statusCode': 200,
            'body': MessageToJson(video_process_result)
        }
    except VimeoUploaderInternalServerError:
        return {
            'headers': {
                'Content-Type': 'text/plain'
            },
            'statusCode': 500,
            'errorMessage': f"Failed to process the video with id {video_id} due to some internal server error"}
