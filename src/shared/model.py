from dataclasses import dataclass


@dataclass
class VideoMetadata:
    """
    Data object for video metadata
    """
    video_id: str
    title: str
    author: str
    length_in_sec: int
    publish_date: str
    resolutions: list


@dataclass
class VideoProcessResult:
    """
    Data object for video processing
    """
    download_url: str
    upload_url: str
