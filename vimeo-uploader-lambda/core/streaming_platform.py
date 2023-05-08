import logging
import os
from abc import abstractmethod, ABC
from datetime import datetime
from enum import Enum

import vimeo
import yt_dlp
from yt_dlp.utils import prepend_extension

from core.exceptions import VimeoUploaderInternalServerError
from core.generated import model_pb2


class SupportedPlatform(Enum):
    YOUTUBE = 1
    VIMEO = 2


class StreamingPlatform(ABC):

    @abstractmethod
    def get_video_metadata(self, video_id) -> model_pb2.VideoMetadata:
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
            start_time_in_sec: int,
            end_time_in_sec: int,
            download_path: str,
            output_file_name: str) -> bool:
        """
        Download the video from streaming service with input parameters to the output path. Output video must contain
        both video and audio channels
        :param video_id: ID of the video
        :param start_time_in_sec: Start time of trim in seconds
        :param end_time_in_sec: End time of trim in seconds
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

    def get_video_metadata(self, video_id) -> model_pb2.VideoMetadata:
        url = self._get_youtube_url(video_id)
        ydl_opts = {
            'cachedir': '/tmp/yt-dlp'
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.sanitize_info(ydl.extract_info(url, download=False))
                return model_pb2.VideoMetadata(
                    video_id=info["id"],
                    title=info["title"],
                    author=info["uploader"],
                    length_in_sec=info["duration"],
                    publish_date=datetime.strptime(
                        info["upload_date"],
                        '%Y%m%d').strftime(DATE_FORMAT))
        except Exception as e:
            raise VimeoUploaderInternalServerError(e)

    def download_video(
            self,
            video_id: str,
            start_time_in_sec: int,
            end_time_in_sec: int,
            download_path: str,
            output_file_name: str) -> bool:
        url = self._get_youtube_url(video_id)

        # Download the video, and trim it using ffmpeg
        # Fetch the best video / audio
        ydl_opts = {
            'format': "bv*+ba/b",
            'outtmpl': os.path.join(download_path, output_file_name),
            'cachedir': '/tmp/yt-dlp',
            'merge_output_format': 'mkv'
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.add_post_processor(
                    self.FFmpegTrimPP(
                        start_time_in_sec,
                        end_time_in_sec))
                error_code = ydl.download(url)
                logging.info("Error code is %d", error_code)
        except Exception as e:
            raise VimeoUploaderInternalServerError(e)
        return True

    def upload_video(self, video_path: str, title: str,
                     image_path: str = None) -> str:
        raise NotImplementedError("This operation is not yet implemented")

    @staticmethod
    def _get_youtube_url(video_id: str) -> str:
        return YOUTUBE_URL_PREFIX + video_id

    class FFmpegTrimPP(yt_dlp.postprocessor.ffmpeg.FFmpegFixupPostProcessor):
        """
        Custom post processor used for trimming video
        """

        def __init__(self, start_time_in_sec: int, end_time_in_sec: int):
            super().__init__()
            self.start_time_in_sec = start_time_in_sec
            self.end_time_in_sec = end_time_in_sec

        def run(self, information):
            output_opts = [
                '-ss', str(self.start_time_in_sec),
                '-to', str(self.end_time_in_sec),
                '-c',
                'copy',
            ]
            filename = information['filepath']
            temp_filename = prepend_extension(filename, 'temp')
            # Ordering of inputs matters!
            self.real_run_ffmpeg([(filename, [])], [
                                 (temp_filename, output_opts)])
            os.replace(temp_filename, filename)
            return [], information


class VimeoPlatform(StreamingPlatform):

    def get_video_metadata(self, video_id) -> model_pb2.VideoMetadata:
        raise NotImplementedError("This operation is not yet implemented")

    def download_video(
            self,
            video_id: str,
            start_time_in_sec: int,
            end_time_in_sec: int,
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
            # Upload the video, and call patch to set title
            url = vimeo_client.upload(video_path)
            vimeo_client.patch(
                url,
                data={
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
