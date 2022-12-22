import os
from os.path import exists
from unittest import mock

from moviepy.video.io.VideoFileClip import VideoFileClip

from src.shared.streaming_platform import YouTubePlatform, VimeoPlatform


def test_youtube_platform_get_video_metadata() -> None:
    platform = YouTubePlatform()
    video_metadata = platform.get_video_metadata("XsX3ATc3FbA")

    assert video_metadata.video_id == "XsX3ATc3FbA"
    assert video_metadata.title == "BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV"
    assert video_metadata.author == "HYBE LABELS"
    assert video_metadata.length_in_sec == 253
    assert video_metadata.publish_date == "2019-04-12"
    assert video_metadata.resolutions == [
        "144p", "240p", "360p", "480p", "720p", "1080p"]


def test_download_youtube_resources_and_combine_short(tmpdir) -> None:
    """
    Test download short resources from YouTube, merging the video/audio.
    :return: Nothing
    """
    # BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV
    _test_download_youtube_resources_and_combine(
        tmpdir, "XsX3ATc3FbA", "1080p", 252)


def test_download_youtube_resources_and_combine_long(tmpdir) -> None:
    """
    Test download long resources from YouTube, merging the video/audio.
    :return: Nothing
    """
    # [LIVE] 로스트아크 특별 방송 | 19:30 ON AIR
    _test_download_youtube_resources_and_combine(
        tmpdir, "Xofxcgkag1M", "1080p", 4190)


def _test_download_youtube_resources_and_combine(
        tmpdir,
        video_id: str,
        video_resolution: str,
        length_in_sec: int) -> None:
    """
    Helper test function for downloading YouTube videos
    :param tmpdir: Temporary test directory
    :param video_id: Test video ID
    :param video_resolution: Test video resolution
    :param length_in_sec: Length for the test video
    """
    platform = YouTubePlatform()
    platform.download_video(
        video_id,
        video_resolution,
        tmpdir,
        "combined_video.mp4")

    expected_combined_path = os.path.join(tmpdir, "combined_video.mp4")
    assert exists(expected_combined_path)
    video = VideoFileClip(expected_combined_path)
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

    upload_data_json = {
        'name': video_title,
        'privacy': {
            'comments': 'nobody'
        }
    }
    client.upload.assert_called_with(video_path, data=upload_data_json)
    client.upload_picture.assert_called_with(
        upload_url, thumbnail_image_path, activate=True)
