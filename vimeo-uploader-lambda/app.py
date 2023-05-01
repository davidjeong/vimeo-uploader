import json
import uuid

from google.protobuf.json_format import MessageToJson

from core.driver import Driver, get_streaming_platform
from core.exceptions import VimeoUploaderInternalServerError, VimeoUploaderInvalidVideoIdError


def handle_get_video_metadata(event, context):
    print(event['queryStringParameters'])
    platform = event['queryStringParameters']['platform']
    video_id = event['queryStringParameters']['video_id']
    driver = Driver(download_platform=get_streaming_platform(platform))
    return _handle_get_video_metadata(driver, video_id)


def _handle_get_video_metadata(
        driver: Driver,
        video_id: str):
    try:
        video_metadata = driver.get_video_metadata(video_id)
        print(f"Retrieved the video metadata for video id {video_id}")
        return {
            'statusCode': 200,
            'headers': {
                "Content-Type": "application/json"
            },
            'body': MessageToJson(video_metadata)
        }
    except VimeoUploaderInvalidVideoIdError:
        return {
            'statusCode': 404,
            'headers': {
                "Content-Type": "application/json"
            },
            'body': json.dumps({
                'error': f"Failed to get metadata with video id {video_id} because it is invalid"
            })
        }
    except VimeoUploaderInternalServerError:
        return {
            'statusCode': 500,
            'headers': {
                "Content-Type": "application/json"
            },
            'body': json.dumps({
                'error': f"Failed to get metadata with video id {video_id} due to some internal server error"
            })
        }


def handle_process_video_upload(event, context):
    print(event['body'])
    download_platform = event['body']['download_platform']
    upload_platform = event['body']['upload_platform']
    video_id = event['body']['video_id']
    start_time_in_sec = event['body']['start_time_in_sec']
    end_time_in_sec = event['body']['end_time_in_sec']
    image_identifier = event['body']['image_identifier']
    title = event['body']['title']
    download = event['body']['download']
    driver = Driver(
        get_streaming_platform(download_platform),
        get_streaming_platform(upload_platform))
    return _handle_process_video_upload(
        driver,
        video_id,
        start_time_in_sec,
        end_time_in_sec,
        image_identifier,
        title,
        download)


def _handle_process_video_upload(
        driver: Driver,
        video_id: str,
        start_time_in_sec: int,
        end_time_in_sec: int,
        image_identifier: str,
        title: str,
        download: bool):
    try:
        video_process_result = driver.process_video(
            video_id,
            start_time_in_sec,
            end_time_in_sec,
            image_identifier,
            title,
            download)
        return {
            'statusCode': 200,
            'headers': {
                "Content-Type": "application/json"
            },
            'body': MessageToJson(video_process_result)
        }
    except VimeoUploaderInternalServerError:
        return {
            'statusCode': 500,
            'headers': {
                "Content-Type": "application/json"
            },
            'body': json.dumps({
                'error': f"Failed to process the video with id {video_id} due to some internal server error"
            })
        }


def handle_upload_thumbnail_image(event, context):
    data = event['body']
    driver = Driver()
    return _handle_upload_thumbnail_image(
        driver, '/tmp', str(uuid.uuid4()), data)


def _handle_upload_thumbnail_image(
        driver: Driver,
        root_path: str,
        object_key: str,
        object_content: str):
    try:
        thumbnail_upload_result = driver.upload_thumbnail_image_to_s3(
            root_path, object_key, object_content)
        return {
            'statusCode': 200,
            'headers': {
                "Content-Type": "application/json"
            },
            'body': MessageToJson(thumbnail_upload_result)
        }
    except VimeoUploaderInternalServerError:
        return {
            'statusCode': 500,
            'headers': {
                "Content-Type": "application/json"
            },
            'body': json.dumps({
                'error': f"Failed to upload the image with key {object_key} at path {object_path} due to some internal server error"
            })
        }
