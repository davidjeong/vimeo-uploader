import boto3
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
            'body': MessageToJson(video_metadata)
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
    print(event['body'])
    download_platform = event['body']['download_platform']
    upload_platform = event['body']['upload_platform']
    video_id = event['body']['video_id']
    start_time_in_sec = event['body']['start_time_in_sec']
    end_time_in_sec = event['body']['end_time_in_sec']
    image_content = event['body']['image_content']
    image_name = event['body']['image_name']
    resolution = event['body']['resolution']
    title = event['body']['title']
    download = event['body']['download']
    s3_client = boto3.client('s3')
    driver = Driver(
        s3_client,
        get_streaming_platform(download_platform),
        get_streaming_platform(upload_platform))
    return _handle_process_video_upload(
        driver,
        video_id,
        start_time_in_sec,
        end_time_in_sec,
        image_content,
        image_name,
        resolution,
        title,
        download)


def _handle_process_video_upload(
        driver: Driver,
        video_id: str,
        start_time_in_sec: int,
        end_time_in_sec: int,
        image_content: str,
        image_name: str,
        resolution: str,
        title: str,
        download: bool):
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
            'statusCode': 200,
            'body': MessageToJson(video_process_result)
        }
    except VimeoUploaderInternalServerError:
        return {
            'statusCode': 500,
            'errorMessage': f"Failed to process the video with id {video_id} due to some internal server error"}
