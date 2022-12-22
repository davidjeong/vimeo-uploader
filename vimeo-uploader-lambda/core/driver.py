import base64
import logging
import os
from datetime import date

import ffmpeg
from botocore.exceptions import NoCredentialsError

from core.exceptions import VimeoUploaderInternalServerError
from core.generated import model_pb2
from core.streaming_platform import SupportedPlatform, YouTubePlatform, VimeoPlatform


class Driver:
    """
    Driver for the video/audio interaction
    """

    def __init__(self, s3_client=None, environment=None) -> None:
        """
        Initialize the driver used to interact with video/audio resources
        """
        self.streaming_platforms = {
            SupportedPlatform.YOUTUBE.name.lower(): YouTubePlatform(),
            SupportedPlatform.VIMEO.name.lower(): VimeoPlatform()
        }
        self.s3_client = s3_client
        self.environment = environment
        print("Driver initialization successful")

    def get_video_metadata(
            self,
            platform: str,
            video_id: str) -> model_pb2.VideoMetadata:
        """
        Get video metadata for supported platform
        :param platform: Supported platform
        :param video_id: ID of the video
        :return: Video metadata from video service for video ID
        """
        return self.streaming_platforms[platform].get_video_metadata(video_id)

    def process_video(
            self,
            download_platform: str,
            upload_platform: str,
            video_id: str,
            start_time_in_sec: int,
            end_time_in_sec: int,
            image_content: bytes,
            image_file_name: str,
            resolution: str,
            title: str,
            download: bool) -> model_pb2.VideoProcessResult:
        """
        Process the video with input video configuration
        :param download_platform: Supported platform for download
        :param upload_platform: Supported platform for upload
        :param video_id: ID of the video
        :param start_time_in_sec: Start time of trim in seconds
        :param end_time_in_sec: End time of trim in seconds
        :param image_content: Content of the thumbnail
        :param image_file_name: Name of the thumbnail image
        :param resolution: Resolution of the final video
        :param title: Title of the video
        :param download: True if download the video, false otherwise
        :return
        """
        if not title:
            today = date.today()
            current_date = today.strftime("%m/%d/%y")
            title = f"(CW) {current_date}"

        suffix = f"{str(start_time_in_sec)}_{str(end_time_in_sec)}_{resolution}"
        combined_video_name = f"combined_{resolution}.mp4"
        trimmed_video_name = f"{video_id}_{suffix}.mp4"
        s3_object_key = f"{video_id}_{suffix}"

        download_path = f"/tmp/{video_id}"
        if not os.path.exists(download_path):
            logging.info("Creating directory %s", download_path)
            os.mkdir(download_path)
        combined_video_path = os.path.join(download_path, combined_video_name)
        trimmed_video_path = os.path.join(download_path, trimmed_video_name)

        downloaded = self.streaming_platforms[download_platform].download_video(
            video_id, resolution, download_path, combined_video_name)

        if not downloaded:
            raise VimeoUploaderInternalServerError(
                "Failed to download the video")

        trim_resource(
            combined_video_path,
            trimmed_video_path,
            start_time_in_sec,
            end_time_in_sec
        )

        logging.info("Finished trimming the video")

        if image_content:
            image_path = self._write_image_stream_to_file(
                image_content, '/tmp', image_file_name)
        else:
            image_path = None

        if self.environment == "production":
            upload_url = self.streaming_platforms[upload_platform].upload_video(
                trimmed_video_path, title, image_path)
        else:
            upload_url = None

        if self.environment == "production" and download:
            download_url = self._upload_file_to_s3(
                s3_object_key, trimmed_video_path)
        else:
            download_url = None

        logging.info("Download link is %s", download_url)
        logging.info("Upload link is %s", upload_url)

        return model_pb2.VideoProcessResult(
            download_url=download_url,
            upload_url=upload_url)

    def _upload_file_to_s3(
            self,
            object_key: str,
            object_path: str,
            expires_in: int = 6 *
            3600) -> str:
        """
        Upload file to S3
        :param object_key: Key of the object
        :param object_path: Path to the object
        :expires_in: Expiry time of object on S3 (in seconds)
        :return
        """
        try:
            self.s3_client.upload_file(object_path,
                                       os.environ['S3_BUCKET_NAME'],
                                       object_key)
            url = self.s3_client.generate_presigned_url(
                ClientMethod='get_object', Params={
                    'Bucket': os.environ['S3_BUCKET_NAME'],
                    'Key': object_key,
                },
                ExpiresIn=expires_in
            )
        except (FileNotFoundError, NoCredentialsError):
            logging.error(
                "Failed to upload object with key % and file %s to s3",
                object_key,
                object_path)
            url = None
        return url

    @staticmethod
    def _write_image_stream_to_file(
            image_content: bytes,
            root_path: str,
            file_name: str) -> str:
        """
        Write image stream to file specified by path
        :param image_content: Content stream of image (in base64)
        :param root_path: Root path of file
        :param file_name: Name of the original file
        :return
        """
        image_path = os.path.join(root_path, file_name)
        with open(image_path, 'wb') as file:
            file.write(base64.decodebytes(image_content))
        return image_path


def trim_resource(
        input_path: str,
        output_path: str,
        start_time_in_sec: int,
        end_time_in_sec: int) -> None:
    """
    Trim the resource based on start and end time in seconds
    :param input_path:
    :param output_path:
    :param start_time_in_sec:
    :param end_time_in_sec:
    :return:
    """
    input_video = ffmpeg.input(input_path)
    ffmpeg.output(
        input_video,
        output_path,
        ss=start_time_in_sec,
        to=end_time_in_sec,
        vcodec='copy',
        acodec='copy').run()