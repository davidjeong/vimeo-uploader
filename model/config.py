"""
Contains all data objects used by application
"""

import os
from dataclasses import dataclass
from datetime import datetime

VIMEO_CONFIG_FILE_NAME = 'vimeo_config.bin'


@dataclass
class AppDirectoryConfiguration:
    """
    Data object for application directory configuration
    """
    root_dir: str
    videos_dir: str
    config_dir: str

    def get_vimeo_config_file_path(self) -> str:
        """
        Get the vimeo config file path
        :return:
        """
        return os.path.join(self.config_dir, VIMEO_CONFIG_FILE_NAME)


@dataclass
class VideoDownloadConfiguration:
    """
    Data object for video download configuration
    """
    video_id: str
    resolution: str


@dataclass
class VideoTrimUploadConfiguration:
    """
    Data object for video trim and upload configuration
    """
    video_id: str
    video_path: str
    start_time_in_sec: int
    end_time_in_sec: int
    video_title: str = None
    image_url: str = None


@dataclass
class VimeoClientConfiguration:
    """
    Data object for vimeo client configuration
    """
    token: str
    key: str
    secret: str


@dataclass
class VideoMetadata:
    """
    Data object for Video metadata
    """
    video_id: str
    title: str
    author: str
    length_in_sec: int
    publish_date: datetime
    resolutions: set
