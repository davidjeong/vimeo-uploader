import os
from os.path import exists
from unittest import mock

from moviepy.video.io.VideoFileClip import VideoFileClip
from mutagen.mp4 import MP4

from core.driver import Driver
from core.streaming_service import VimeoService, SupportedServices
from model.config import VideoTrimUploadConfiguration, AppDirectoryConfiguration, VideoDownloadConfiguration


def test_workflow_short(tmpdir) -> None:
    """
    Test download short resources from YouTube, merging the video/audio and trim.
    :return: Nothing
    """
    # BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV
    _test_download_trim_workflow(
        tmpdir, "XsX3ATc3FbA", "bts_video", "1080p", 252, 60, 120)


def test_workflow_long(tmpdir) -> None:
    """
    Test download long resources from YouTube, merging the video/audio and trim.
    :return: Nothing
    """
    # [LIVE] 로스트아크 특별 방송 | 19:30 ON AIR
    _test_download_trim_workflow(
        tmpdir, "Xofxcgkag1M", "lost_ark_video", "1080p", 4190, 1445, 3887)


def test_upload_video_to_vimeo() -> None:
    """
    Test uploading video to vimeo using mock client
    :return: Nothing
    """
    client_config = mock.MagicMock()
    client = mock.MagicMock()
    video_path = "/path/to/video"
    video_title = "new title"

    service = VimeoService()
    service.update_client_config(client_config)
    service._upload_video(client, video_path, video_title)

    data_json = {
        'name': video_title,
        'privacy': {
            'comments': 'nobody'
        }
    }
    client.upload.assert_called_with(video_path, data=data_json)


def _test_download_trim_workflow(
        tmpdir,
        test_video_id: str,
        test_video_title: str,
        test_video_resolution: str,
        original_length: int,
        trim_start_sec: int,
        trim_end_sec: int) -> None:
    """
    Helper test driver for downloading and trimming YouTube videos
    :param tmpdir: Temporary test directory
    :param test_video_id: Test video ID
    :param test_video_title: Title of test video
    :param test_video_resolution: Test video resolution
    :param original_length: Length for the test video
    """

    # Create the app directory configuration
    app_directory_configuration = AppDirectoryConfiguration(None, tmpdir, None)

    # Create the video download configuration
    video_download_configuration = VideoDownloadConfiguration(
        test_video_id, test_video_resolution)

    # Create the driver
    driver = Driver()
    driver.update_download_service(SupportedServices.YOUTUBE)
    driver.update_upload_service(SupportedServices.VIMEO)
    driver.update_app_directory_config(app_directory_configuration)

    expected_video_stream_path = os.path.join(
        tmpdir, test_video_id, 'video_stream_1080p.mp4')
    expected_audio_stream_path = os.path.join(
        tmpdir, test_video_id, 'audio_stream.mp3')

    # Download the video
    driver.download(video_download_configuration)

    assert exists(expected_video_stream_path)
    video = VideoFileClip(expected_video_stream_path)
    assert int(video.duration) == original_length

    assert exists(expected_audio_stream_path)
    audio = MP4(expected_audio_stream_path)
    assert int(audio.info.length) == original_length

    combined_path = os.path.join(
        tmpdir,
        test_video_id,
        f"combined_{test_video_resolution}.mp4")
    final_path = os.path.join(
        tmpdir,
        test_video_id,
        f"{trim_start_sec}_{trim_end_sec}_{test_video_resolution}.mp4")

    assert exists(combined_path)
    video = VideoFileClip(combined_path)
    assert int(video.duration) == original_length
    assert int(video.audio.duration) == original_length

    # Create the video trim configuration
    video_trim_configuration = VideoTrimUploadConfiguration(
        test_video_id,
        combined_path,
        test_video_resolution,
        trim_start_sec,
        trim_end_sec,
        test_video_title,
        None)

    # Trim the video
    driver.trim_resource(video_trim_configuration)

    assert exists(final_path)
    video = VideoFileClip(final_path)
    trim_length = trim_end_sec - trim_start_sec
    # trim_length <= video_duration <= trim_length + 1
    assert trim_length <= int(video.duration) <= trim_length + 1
    assert trim_length <= int(video.duration) <= trim_length + 1
