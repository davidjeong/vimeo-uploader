import json
import logging
from typing import Optional

import boto3
from botocore.client import logger
from botocore.exceptions import ClientError
from google.protobuf.json_format import ParseDict

from generated import model_pb2

logging.basicConfig(
    filename='output.log',
    encoding='utf-8',
    level=logging.INFO)


class VimeoUploaderLambdaClient:
    """
    Python client for communicating with AWS Lambda functions
    """

    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str):
        """
        Initialize the client with AWS credentials
        :param aws_access_key_id: AWS access key id
        :param aws_secret_access_key: AWS secret access key
        """
        self.lambda_client = boto3.client(
            'lambda',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name='us-east-1'
        )

    def get_video_metadata(
            self,
            platform: str,
            video_id: str) -> Optional[model_pb2.VideoMetadata]:
        try:
            response = self.lambda_client.invoke(
                FunctionName="get-video-metadata",
                Payload=json.dumps({
                    "queryStringParameters": {
                        "platform": platform,
                        "video_id": video_id
                    }
                }))
            logger.info("Invoked function get-video-metadata")
        except ClientError:
            logger.exception("Couldn't invoke function get-video-metadata")
            return None
        payload = json.loads(response['Payload'].read())
        if payload["statusCode"] == 200:
            video_metadata = ParseDict(
                json.loads(
                    payload["body"]),
                model_pb2.VideoMetadata())
            return video_metadata
        elif payload["statusCode"] == 404:
            logging.info(f"Video with id {video_id} is not available")
            return None

    def process_video(
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
            download: bool) -> Optional[model_pb2.VideoProcessResult]:
        try:
            response = self.lambda_client.invoke(
                FunctionName="process-video",
                Payload=json.dumps({
                    "body": {
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
                    }
                }))
            logger.info("Invoked function get-video-metadata")
        except ClientError:
            logger.exception("Couldn't invoke function get-video-metadata")
            return None
        payload = json.loads(response['Payload'].read())
        if payload["statusCode"] == 200:
            video_process_result = ParseDict(
                json.loads(payload["body"]), model_pb2.VideoProcessResult()
            )
            return video_process_result
        elif payload["statusCode"] == 500:
            logging.error(f"Video with id {video_id} failed to process")
            return None
