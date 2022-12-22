from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class VideoMetadata(_message.Message):
    __slots__ = ["author", "length_in_sec", "publish_date", "resolutions", "title", "video_id"]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    LENGTH_IN_SEC_FIELD_NUMBER: _ClassVar[int]
    PUBLISH_DATE_FIELD_NUMBER: _ClassVar[int]
    RESOLUTIONS_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    VIDEO_ID_FIELD_NUMBER: _ClassVar[int]
    author: str
    length_in_sec: int
    publish_date: str
    resolutions: _containers.RepeatedScalarFieldContainer[str]
    title: str
    video_id: str
    def __init__(self, video_id: _Optional[str] = ..., title: _Optional[str] = ..., author: _Optional[str] = ..., length_in_sec: _Optional[int] = ..., publish_date: _Optional[str] = ..., resolutions: _Optional[_Iterable[str]] = ...) -> None: ...

class VideoProcessResult(_message.Message):
    __slots__ = ["download_url", "upload_url"]
    DOWNLOAD_URL_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_URL_FIELD_NUMBER: _ClassVar[int]
    download_url: str
    upload_url: str
    def __init__(self, download_url: _Optional[str] = ..., upload_url: _Optional[str] = ...) -> None: ...
