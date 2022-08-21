"""
This is the script to
1. download the video from YouTube in 1440p/1080p
2. download the audio for video separately
3. merge the audio and video
4. trim the merged video using start and end timestamp
5. upload the video to vimeo with supplied date
6. edit the video thumbnail
"""
import argparse
import logging
import os.path
import sys

import ffmpeg
import pytube
import vimeo

from core.streaming_service import YouTubeService, VimeoService, SupportedServices
from core.util import get_vimeo_client_configuration
from model.config import VimeoClientConfiguration, AppDirectoryConfiguration, VideoMetadata, VideoDownloadConfiguration, \
    VideoTrimUploadConfiguration
from model.exception import UnsetConfigurationException, VideoDownloadFailedException

logging.basicConfig(
    filename='output.log',
    encoding='utf-8',
    level=logging.INFO)


class Driver:
    """
    Driver for the video/audio interaction
    """

    def __init__(self) -> None:
        """
        Initialize the driver used to interact with video/audio resources
        """
        self.app_directory_config = None
        self.streaming_services = {
            SupportedServices.YOUTUBE: YouTubeService(),
            SupportedServices.VIMEO: VimeoService()
        }
        self.download_service = None
        self.upload_service = None

    def update_vimeo_client_config(
            self, client_config: VimeoClientConfiguration) -> None:
        """
        Update vimeo client configuration
        :param client_config: Configuration for Vimeo client
        :return:
        """
        self.streaming_services[SupportedServices.VIMEO].update_client_config(
            client_config)

    def update_app_directory_config(
            self, app_directory_config: AppDirectoryConfiguration) -> None:
        """
        Update application directory configuration
        :param app_directory_config:
        :return
        """
        self.app_directory_config = app_directory_config

    def update_download_service(self, download_service: SupportedServices):
        self.download_service = download_service

    def update_upload_service(self, upload_service: SupportedServices):
        self.upload_service = upload_service

    def get_video_metadata(
            self,
            video_service: SupportedServices,
            video_id: str) -> VideoMetadata:
        """
        Get video metadata for supported service
        :param video_service: Service to get video metadata for
        :param video_id: ID of the video
        :return: Video metadata from video service for video ID
        """
        return self.streaming_services[video_service].get_video_metadata(
            video_id)

    def download(
            self,
            video_download_config: VideoDownloadConfiguration) -> str:
        """
        Download the video with input video configuration
        :param video_download_config:
        :return Combined video path
        """
        if self.app_directory_config is None:
            raise UnsetConfigurationException(
                "App directory config is not set")

        if self.download_service is None or self.upload_service is None:
            raise UnsetConfigurationException(
                "Download service or upload service is not set")

        video_id = video_download_config.video_id
        resolution = video_download_config.resolution

        combined_video_name = f"combined_{resolution}.mp4"

        download_path = os.path.join(
            self.app_directory_config.videos_dir, video_id)
        if not os.path.exists(download_path):
            logging.info("Creating directory %s", download_path)
            os.mkdir(download_path)
        combined_video_path = os.path.join(download_path, combined_video_name)

        try:
            self.streaming_services[self.download_service].download_video(
                video_id, resolution, download_path, combined_video_name)
        except Exception as error:
            raise VideoDownloadFailedException(
                f"Failed to download video with id {video_id} and resolution {resolution} with error {error}")

        return combined_video_path

    def trim_resource(
            self,
            video_trim_upload_config: VideoTrimUploadConfiguration) -> str:
        """
        Trim the resource based on start and end time in seconds
        :param video_trim_upload_config
        :return: Trimmed video path
        """
        video_id = video_trim_upload_config.video_id
        video_resolution = video_trim_upload_config.video_resolution
        input_path = video_trim_upload_config.video_path
        start_time_in_sec = video_trim_upload_config.start_time_in_sec
        end_time_in_sec = video_trim_upload_config.end_time_in_sec

        if self.app_directory_config is None:
            raise UnsetConfigurationException(
                "App directory config is not set")

        trimmed_path = os.path.join(
            self.app_directory_config.videos_dir, video_id)

        prefix = f"{str(start_time_in_sec)}_{str(end_time_in_sec)}_{video_resolution}"
        trimmed_video_name = f"{prefix}.mp4"
        trimmed_video_path = os.path.join(trimmed_path, trimmed_video_name)

        # Call ffmpeg to trim.
        if not os.path.exists(trimmed_video_path):
            input_video = ffmpeg.input(input_path)
            ffmpeg.output(
                input_video,
                trimmed_video_path,
                ss=start_time_in_sec,
                to=end_time_in_sec,
                vcodec='copy',
                acodec='copy').run()
            logging.info("Finished trimming the video")

        # Return trimmed video path
        return trimmed_video_path

    def upload_video(
            self,
            video_path: str,
            video_title: str,
            image: str) -> str:
        """
        Uploads the video to using upload service
        :param video_path:
        :param video_title:
        :param image:
        :return: Url of the uploaded video
        """
        logging.info(
            'Uploading video to upload service from path: %s',
            video_path)

        return self.streaming_services[self.upload_service].upload_video(
            video_path, video_title, image)


def main() -> None:
    """
    Main program for command-line based execution
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v',
        '--video_id',
        help='ID for YouTube video',
        required=True)
    parser.add_argument(
        '-s',
        '--start',
        help='Start time of video in format 00:00:00',
        required=True)
    parser.add_argument(
        '-e',
        '--end',
        help='End time of video in format 00:00:00',
        required=True)
    parser.add_argument(
        '-c',
        '--config',
        help='Path to the config required by Vimeo',
        required=True)
    parser.add_argument(
        '-i',
        '--image',
        help='Path to the thumbnail image of the video')
    parser.add_argument(
        '-r',
        '--resolution',
        help='Resolution of the video',
        default='1080p')
    parser.add_argument('-t', '--title', help='Title of the video')
    args = parser.parse_args()

    vimeo_config = get_vimeo_client_configuration(args.config)

    try:
        video_config = VideoDownloadConfiguration(
            args.video_id, args.resolution)
    except (pytube.exceptions.PytubeError, vimeo.exceptions.VideoUploadFailure) as error:
        logging.error("Failed with exception %s", error)
        sys.exit(1)

    driver = Driver()
    driver.update_download_service(SupportedServices.YOUTUBE)
    driver.update_upload_service(SupportedServices.VIMEO)
    driver.update_vimeo_client_config(vimeo_config)

    try:
        driver.process(video_config)
    except vimeo.exceptions.VideoUploadFailure as error:
        logging.error("Failed with exception %s", error)
        sys.exit(1)


if __name__ == "__main__":
    main()
