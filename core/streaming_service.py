import logging
import os
from abc import ABC, abstractmethod
from enum import Enum

import ffmpeg
import pytube
import vimeo
from pytube.cli import on_progress

from model.config import VideoMetadata, VimeoClientConfiguration
from model.exception import VimeoClientConfigurationException


class SupportedServices(Enum):
    YOUTUBE = 1
    VIMEO = 2


class StreamingService(ABC):
    """
    Interface for defining a video streaming endpoint (e.g. YouTube, Vimeo)
    """

    @abstractmethod
    def get_video_metadata(self, video_id) -> VideoMetadata:
        """
        Get the metadata about the video
        :param video_id: ID of the video
        :return: Metadata for the video
        """
        pass

    @abstractmethod
    def download_video(
            self,
            video_id: str,
            resolution: str,
            download_path: str,
            output_file_name: str) -> bool:
        """
        Download the video from streaming service with input parameters to the output path. Output video must contain
        both video and audio channels.
        :param video_id: ID of the video
        :param resolution: Resolution for the video (e.g. 1080p, 1440p)
        :param download_path: Absolute path to the output destination folder
        :param output_file_name: Name of the output video file
        :return: Boolean flag representing whether the video completed downloading
        """
        pass

    @abstractmethod
    def upload_video(self, video_path: str, video_title: str,
                     thumbnail_image_path: str = None) -> bool:
        """
        Upload the video to streaming service.
        :param video_path: Absolute path to the video
        :param video_title: Title of the uploaded video
        :param thumbnail_image_path: Absolute path to the thumbnail image
        :return: Boolean flag representing whether the video uploaded successfully
        """
        pass


YOUTUBE_URL_PREFIX: str = "https://www.youtube.com/watch?v="


class YouTubeService(StreamingService):

    def get_video_metadata(self, video_id) -> VideoMetadata:
        url = self._get_youtube_url(video_id)
        try:
            youtube = pytube.YouTube(url, on_progress_callback=on_progress)
            return VideoMetadata(
                youtube.video_id,
                youtube.title,
                youtube.author,
                youtube.length,
                youtube.publish_date,
                set([stream.resolution for stream in youtube.streams])
            )
        except pytube.exceptions.PytubeError as error:
            logging.error("Failed to get metadata with video id %s", video_id)
            raise error

    def download_video(
            self,
            video_id: str,
            resolution: str,
            download_path: str,
            output_file_name: str) -> bool:
        url = self._get_youtube_url(video_id)
        video_stream_file_name = self._get_video_stream_file_name(resolution)
        audio_stream_file_name = self._get_audio_stream_file_name()
        # Download the separate video/audio streams
        try:
            youtube = pytube.YouTube(
                url, on_progress_callback=on_progress)
            video_stream = youtube.streams.filter(
                resolution=resolution).first()
            video_stream.download(download_path, video_stream_file_name)
            audio_stream = youtube.streams.filter(only_audio=True).first()
            audio_stream.download(download_path, audio_stream_file_name)
        except pytube.exceptions.PytubeError as error:
            logging.error(
                "Failed to download video stream or audio stream file from YouTube %s",
                error)
            raise error

        absolute_video_stream_path = os.path.join(
            download_path, video_stream_file_name)
        absolute_audio_stream_path = os.path.join(
            download_path, audio_stream_file_name)
        absolute_output_path = os.path.join(download_path, output_file_name)

        # Combine the two streams into one using FFMPEG
        input_video_stream = ffmpeg.input(absolute_video_stream_path)
        input_audio_stream = ffmpeg.input(absolute_audio_stream_path)
        ffmpeg.output(
            input_video_stream,
            input_audio_stream,
            absolute_output_path,
            vcodec='copy').run()
        return True

    def upload_video(
            self,
            video_path: str,
            video_title: str,
            thumbnail_image_path: str = None) -> bool:
        raise NotImplementedError(
            "This operation is not yet implemented for YouTubeService.")

    @staticmethod
    def _get_youtube_url(video_id: str) -> str:
        return YOUTUBE_URL_PREFIX + video_id

    @staticmethod
    def _get_video_stream_file_name(resolution: str) -> str:
        return f"video_stream_{resolution}.mp4"

    @staticmethod
    def _get_audio_stream_file_name() -> str:
        return "audio_stream.mp3"


class VimeoService(StreamingService):

    def __init__(self):
        self.client_config = None

    def get_video_metadata(self, video_id) -> VideoMetadata:
        raise NotImplementedError(
            "This operation is not yet implemented for VimeoService.")

    def download_video(
            self,
            video_id: str,
            resolution: str,
            download_path: str,
            output_file_name: str) -> bool:
        raise NotImplementedError(
            "This operation is not yet implemented for VimeoService")

    def upload_video(self, video_path: str, video_title: str,
                     thumbnail_image_path: str = None) -> bool:
        # First check if client config is set, otherwise raise exception
        if self.client_config is None:
            raise VimeoClientConfigurationException(
                "Vimeo client configuration is not set")
        # Call internal method
        return self._upload_video(
            vimeo.VimeoClient(
                token=self.client_config.token,
                key=self.client_config.key,
                secret=self.client_config.secret),
            video_path,
            video_title,
            thumbnail_image_path)

    @staticmethod
    def _upload_video(
            vimeo_client: vimeo.VimeoClient,
            video_path: str,
            video_title: str,
            thumbnail_image_path: str = None) -> bool:
        # Try uploading the video using Vimeo client
        try:
            url = vimeo_client.upload(video_path, data={
                'name': video_title,
                'privacy': {
                    'comments': 'nobody'
                }
            })
        except vimeo.exceptions.VideoUploadFailure as error:
            logging.error(
                "Failed to upload video from path %s with title %s - %s",
                video_path,
                video_title,
                error)
            raise error

        # Set the thumbnail image on video if exists
        if url is not None and thumbnail_image_path:
            vimeo_client.upload_picture(
                url, thumbnail_image_path, activate=True)

        video_data = vimeo_client.get(f"{url}?fields=transcode.status").json
        logging.info("The transcode status for %s is %s",
                     url, video_data['transcode']['status'])

        return True

    def update_client_config(self, client_config: VimeoClientConfiguration):
        self.client_config = client_config
