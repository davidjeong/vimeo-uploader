import logging
import os
from datetime import date

import boto3
from botocore.client import BaseClient
from botocore.exceptions import NoCredentialsError

from core.exceptions import VimeoUploaderInternalServerError
from core.generated import model_pb2
from core.streaming_platform import YouTubePlatform, VimeoPlatform, StreamingPlatform, SupportedPlatform

STREAMING_PLATFORMS = {
    SupportedPlatform.YOUTUBE.name.lower(): YouTubePlatform(),
    SupportedPlatform.VIMEO.name.lower(): VimeoPlatform()
}


def get_streaming_platform(platform: str) -> StreamingPlatform:
    """
    Fetch streaming platform from platform string.

    :param platform: Platform string
    :return:
    """
    return STREAMING_PLATFORMS.get(platform)


class Driver:
    """
    Main driver for the video/audio interaction.
    """

    def __init__(
            self,
            download_platform: StreamingPlatform = None,
            upload_platform: StreamingPlatform = None,
            s3_client: BaseClient = boto3.client('s3'),
            allow_download=True,
            allow_upload=True) -> None:
        """
        Initialize the driver used to interact with video/audio resources.
        """
        self.download_platform = download_platform
        self.upload_platform = upload_platform
        self.s3_client = s3_client
        self.allow_download = allow_download
        self.allow_upload = allow_upload
        print("Driver initialization successful")

    def get_video_metadata(
            self,
            video_id: str) -> model_pb2.VideoMetadata:
        """
        Get video metadata from download platform.
        :param video_id: ID of the video
        :return: Video metadata from video service for video ID
        """
        return self.download_platform.get_video_metadata(video_id)

    def process_video(
            self,
            video_id: str,
            start_time_in_sec: int,
            end_time_in_sec: int,
            image_identifier: str,
            title: str,
            download: bool) -> model_pb2.VideoProcessResult:
        """
        Process the video with input video configuration.

        :param video_id: ID of the video
        :param start_time_in_sec: Start time of trim in seconds
        :param end_time_in_sec: End time of trim in seconds
        :param image_identifier: Unique identifier on S3, for image
        :param title: Title of the video
        :param download: True if download the video, false otherwise
        :return:
        """
        if not title:
            today = date.today()
            current_date = today.strftime("%m/%d/%y")
            title = f"(CW) {current_date}"

        suffix = f"{str(start_time_in_sec)}_{str(end_time_in_sec)}"
        video_name = f"{video_id}_{suffix}.mp4"
        s3_object_key = f"{video_id}_{suffix}"
        download_path = os.path.join("/tmp", video_id)

        downloaded = self.download_platform.download_video(
            video_id, start_time_in_sec, end_time_in_sec, download_path, video_name)

        if not downloaded:
            raise VimeoUploaderInternalServerError(
                "Failed to download the video")

        video_path = os.path.join(download_path, video_name)

        if image_identifier:
            image_path = self._download_image_to_file(image_identifier, '/tmp')
        else:
            image_path = None

        if self.allow_upload:
            upload_url = self.upload_platform.upload_video(
                video_path, title, image_path)
        else:
            upload_url = None

        if self.allow_download and download:
            download_url = self._upload_file_to_s3(
                s3_object_key, video_path, os.environ['S3_VIDEO_BUCKET_NAME'])
        else:
            download_url = None

        logging.info("Download link is %s", download_url)
        logging.info("Upload link is %s", upload_url)

        return model_pb2.VideoProcessResult(
            download_url=download_url,
            upload_url=upload_url)

    def upload_thumbnail_image_to_s3(
            self,
            object_key: str,
            object_path: str) -> model_pb2.ThumbnailUploadResult:
        """
        Upload thumbnail image to s3
        """
        s3_url = self._upload_file_to_s3(
            object_key,
            object_path,
            os.environ['S3_THUMBNAIL_BUCKET_NAME'])
        return model_pb2.ThumbnailUploadResult(
            object_key=object_key,
            s3_url=s3_url
        )

    def _upload_file_to_s3(
            self,
            object_key: str,
            object_path: str,
            bucket_name: str,
            expires_in: int = 6 * 3600) -> str:
        """
        Upload file to S3 (with image identifier).

        :param object_key: Key of the object
        :param object_path: Path to the object
        :expires_in: Expiry time of object on S3 (in seconds)
        :return:
        """
        try:
            self.s3_client.upload_file(object_path,
                                       bucket_name,
                                       object_key)
            url = self.s3_client.generate_presigned_url(
                ClientMethod='get_object', Params={
                    'Bucket': bucket_name,
                    'Key': object_key,
                },
                ExpiresIn=expires_in
            )
        except (FileNotFoundError, NoCredentialsError):
            logging.error(
                "Failed to upload object with key % and file %s to s3",
                object_key,
                object_path)
            raise VimeoUploaderInternalServerError(
                "Failed to upload the file to s3")
        return url

    def _download_image_to_file(
            self,
            image_identifier: str,
            root_path: str) -> str:
        """
        Download image from S3 (with image identifier) to disk.

        :param image_identifier: Image identifier on S3.
        :param root_path: Root path of file
        :return:
        """
        image_path = os.path.join(root_path, image_identifier)
        self.s3_client.download_file(
            os.environ['S3_THUMBNAIL_BUCKET_NAME'],
            image_identifier,
            image_path)
        return image_path
