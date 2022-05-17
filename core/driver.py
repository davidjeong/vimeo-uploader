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
from datetime import date

import ffmpeg
import pytube
import vimeo

from core.streaming_service import YouTubeService, VimeoService, StreamingService, SupportedServices
from core.util import get_vimeo_client_configuration, get_video_configuration
from model.config import VimeoClientConfiguration, AppDirectoryConfiguration, VideoConfiguration, VideoMetadata
from model.exception import UnsetConfigurationException

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

    def update_download_service(self, download_service: StreamingService):
        self.download_service = download_service

    def update_upload_service(self, upload_service: StreamingService):
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

    def process(self, video_config: VideoConfiguration) -> None:
        """
        Process the video with input video configuration
        :param video_config:
        :return
        """
        if self.app_directory_config is None:
            raise UnsetConfigurationException(
                "App directory config is not set")

        if self.download_service is None or self.upload_service is None:
            raise UnsetConfigurationException(
                "Download service or upload service is not set")

        video_id = video_config.video_id
        start_time_in_sec = video_config.start_time_in_sec
        end_time_in_sec = video_config.end_time_in_sec
        image = video_config.image_url
        resolution = video_config.resolution
        title = video_config.video_title

        if title is None or not title:
            today = date.today()
            current_date = today.strftime("%m/%d/%y")
            title = f"(CW) {current_date}"

        suffix = f"{str(video_config.start_time_in_sec)}_{str(video_config.end_time_in_sec)}"
        combined_video_name = f"combined_{resolution}.mp4"
        trimmed_video_name = f"{suffix}_{resolution}.mp4"

        download_path = os.path.join(
            self.app_directory_config.videos_dir, video_id)
        if not os.path.exists(download_path):
            logging.info("Creating directory %s", download_path)
            os.mkdir(download_path)
        combined_video_path = os.path.join(download_path, combined_video_name)
        trimmed_video_path = os.path.join(download_path, trimmed_video_name)

        self.streaming_services[self.download_service].download_video(
            video_id, resolution, download_path, combined_video_name)

        # Call ffmpeg to trim.
        if not os.path.exists(trimmed_video_path):
            trim_resource(
                combined_video_path,
                trimmed_video_path,
                start_time_in_sec,
                end_time_in_sec)
            logging.info("Finished trimming the video")

        logging.info(
            'Uploading video to upload service from path: %s',
            trimmed_video_path)

        self.streaming_services[self.upload_service].upload_video(
            trimmed_video_path, title, image)


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
        t=end_time_in_sec,
        vcodec='copy',
        acodec='copy').run()


def main() -> None:
    """
    Main program for command-line based execution
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-u',
        '--url',
        help='URL for YouTube video',
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
        video_config = get_video_configuration(
            args.url,
            args.start,
            args.end,
            args.resolution,
            args.title,
            args.image)
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
