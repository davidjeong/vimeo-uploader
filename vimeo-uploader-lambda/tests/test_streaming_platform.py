import os
from os.path import exists
from unittest import mock

from moviepy.video.io.VideoFileClip import VideoFileClip

from core.streaming_platform import YouTubePlatform, VimeoPlatform


def test_youtube_platform_get_video_metadata() -> None:
    platform = YouTubePlatform()
    video_metadata = platform.get_video_metadata("XsX3ATc3FbA")

    assert video_metadata.video_id == "XsX3ATc3FbA"
    assert video_metadata.title == "BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV"
    assert video_metadata.author == "HYBE LABELS"
    assert video_metadata.length_in_sec == 253
    assert video_metadata.publish_date == "2019-04-12"


def test_download_youtube_resources_short(tmpdir) -> None:
    """
    Test download short resources from YouTube, merging the video/audio, then trimming.
    :return: Nothing
    """
    # BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV
    _test_download_youtube_resources(
        tmpdir, "XsX3ATc3FbA", 60, 120, 60)


def test_download_youtube_resources_long(tmpdir) -> None:
    """
    Test download long resources from YouTube, merging the video/audio, then trimming.
    :return: Nothing
    """
    # [LIVE] 로스트아크 특별 방송 | 19:30 ON AIR
    _test_download_youtube_resources(
        tmpdir, "Xofxcgkag1M", 900, 2700, 1800)


def _test_download_youtube_resources(
        tmpdir,
        video_id: str,
        start_time_in_sec: int,
        end_time_in_sec: int,
        length_in_sec: int) -> None:
    """
    Helper test function for downloading YouTube videos
    :param tmpdir: Temporary test directory
    :param video_id: Test video ID
    :param start_time_in_sec: Start time of trim in seconds
    :param end_time_in_sec: End time of trim in seconds
    :param length_in_sec: Length for the test video
    """
    platform = YouTubePlatform()
    platform.download_video(
        video_id,
        start_time_in_sec,
        end_time_in_sec,
        tmpdir,
        "video.mp4")

    expected_video_path = os.path.join(tmpdir, "video.mp4")
    assert exists(expected_video_path)
    video = VideoFileClip(expected_video_path)
    assert int(video.duration) == length_in_sec
    assert int(video.audio.duration) == length_in_sec


def test_upload_video_to_vimeo() -> None:
    """
    Test uploading video to vimeo using mock client
    :return: Nothing
    """
    client = mock.MagicMock()
    upload_url = "https://vimeo.com/video_id"
    client.upload.return_value = upload_url
    video_path = "/tmp/video_id/combined.mp4"
    video_title = "video title"
    thumbnail_image_path = 'tmp/image.png'

    platform = VimeoPlatform()
    platform._upload_video(
        client,
        video_path,
        video_title,
        thumbnail_image_path)

    patch_data_json = {
        'name': video_title,
        'privacy': {
            'comments': 'nobody'
        }
    }

    client.upload.assert_called_with(video_path)
    client.patch.assert_called_with(upload_url, data=patch_data_json)
    client.upload_picture.assert_called_with(
        upload_url, thumbnail_image_path, activate=True)
