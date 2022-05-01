import os
from dataclasses import dataclass

VIDEO_CONFIG_FILE_NAME = 'vimeo_config.yaml'


@dataclass
class AppDirectoryConfiguration:
    root_dir: str
    videos_dir: str
    config_dir: str

    def get_vimeo_config_file_path(self) -> str:
        return os.path.join(self.config_dir, VIDEO_CONFIG_FILE_NAME)


@dataclass
class VideoConfiguration:

    video_id: str
    start_time_in_sec: int
    end_time_in_sec: int
    resolution: str
    video_title: str = None
    image_url: str = None


@dataclass
class VimeoConfiguration:

    token: str
    key: str
    secret: str


@dataclass
class YoutubeVideoMetadata:

    video_id: str
    title: str
    author: str
    length_in_sec: int
    publish_date: str
