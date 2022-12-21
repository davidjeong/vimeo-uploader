import logging
import os
from abc import abstractmethod, ABC
from enum import Enum
from urllib.error import HTTPError

import ffmpeg
import pytube as pytube
import vimeo

from src.shared.exceptions import VimeoUploaderInternalServerError, VimeoUploaderInvalidVideoIdError
from src.shared.model import VideoMetadata


class SupportedPlatform(Enum):
    YOUTUBE = 1
    VIMEO = 2


class StreamingPlatform(ABC):

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
        both video and audio channels
        :param video_id: ID of the video
        :param resolution: Resolution for the video (e.g. 1080p, 1440p)
        :param download_path: Absolute path to the output destination folder
        :param output_file_name: Name of the output video file
        :return: Boolean flag representing whether the video completed downloading
        """
        pass

    @abstractmethod
    def upload_video(self, video_path: str, title: str,
                     image_path: str = None) -> str:
        """
        Upload the video to streaming service
        :param video_path: Absolute path to the video
        :param title: Title of the uploaded video
        :param image_path: Path of the thumbnail image
        :return: URL of the uploaded video
        """
        pass


YOUTUBE_URL_PREFIX: str = "https://www.youtube.com/watch?v="
DATE_FORMAT: str = "%Y-%m-%d"


class YouTubePlatform(StreamingPlatform):

    def get_video_metadata(self, video_id) -> VideoMetadata:
        def _get_resolution_sort_key(res: str) -> int:
            return int(res[:-1])

        url = self._get_youtube_url(video_id)
        try:
            print(f"Calling to get video metadata for url {url}")
            youtube = pytube.YouTube(url)
            return VideoMetadata(
                youtube.video_id,
                youtube.title,
                youtube.author,
                youtube.length,
                youtube.publish_date.strftime(DATE_FORMAT),
                list(sorted(set(
                    [stream.resolution for stream in youtube.streams if stream.resolution]),
                    key=_get_resolution_sort_key))
            )
        except pytube.exceptions.PytubeError:
            logging.error("Failed to get metadata with video id %s", video_id)
            raise VimeoUploaderInvalidVideoIdError(
                f"Failed to get metadata with video id {video_id}")
        except HTTPError:
            logging.error("Failed to get metadata with video id %s", video_id)
            raise VimeoUploaderInternalServerError(
                f"Failed to get metadata with video id {video_id}")

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
            youtube = pytube.YouTube(url)
            video_stream = youtube.streams.filter(
                resolution=resolution).first()
            video_stream.download(download_path, video_stream_file_name)
            audio_stream = youtube.streams.filter(only_audio=True).first()
            audio_stream.download(download_path, audio_stream_file_name)
        except pytube.exceptions.PytubeError:
            logging.error(
                "Failed to download video/audio stream file from Youtube for url %s", url)
            raise VimeoUploaderInternalServerError(
                f"Failed to download video/audio stream file from Youtube for url {url}")

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

        # Delete the two resource paths
        os.remove(absolute_video_stream_path)
        os.remove(absolute_audio_stream_path)
        return True

    def upload_video(self, video_path: str, title: str,
                     image_path: str = None) -> str:
        raise NotImplementedError("This operation is not yet implemented")

    @staticmethod
    def _get_youtube_url(video_id: str) -> str:
        return YOUTUBE_URL_PREFIX + video_id

    @staticmethod
    def _get_video_stream_file_name(resolution: str) -> str:
        return f"video_stream_{resolution}.mp4"

    @staticmethod
    def _get_audio_stream_file_name() -> str:
        return "audio_stream.mp3"


class VimeoPlatform(StreamingPlatform):

    def get_video_metadata(self, video_id) -> VideoMetadata:
        raise NotImplementedError("This operation is not yet implemented")

    def download_video(
            self,
            video_id: str,
            resolution: str,
            download_path: str,
            output_file_name: str) -> bool:
        raise NotImplementedError("This operation is not yet implemented")

    def upload_video(self, video_path: str, title: str,
                     image_path: str = None) -> str:
        return self._upload_video(
            vimeo.VimeoClient(
                token=os.environ['VIMEO_CLIENT_TOKEN'],
                key=os.environ['VIMEO_CLIENT_KEY'],
                secret=os.environ['VIMEO_CLIENT_SECRET']
            ),
            video_path,
            title,
            image_path)

    @staticmethod
    def _upload_video(
            vimeo_client: vimeo.VimeoClient,
            video_path: str,
            title: str,
            thumbnail_image_path: str = None) -> str:
        try:
            url = vimeo_client.upload(video_path, data={
                'name': title,
                'privacy': {
                    'comments': 'nobody'
                }
            })
        except vimeo.exceptions.VideoUploadFailure:
            logging.error(
                "Failed to upload video from path %s",
                video_path
            )
            raise VimeoUploaderInternalServerError(
                f"Failed to upload video from path {video_path}")

        if url and thumbnail_image_path:
            vimeo_client.upload_picture(
                url, thumbnail_image_path, activate=True)

        video_data = vimeo_client.get(url + '?fields=link').json()
        upload_url = video_data['link']
        return upload_url
