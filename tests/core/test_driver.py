import os
from os.path import exists
from unittest import mock

from moviepy.video.io.VideoFileClip import VideoFileClip
from mutagen.mp4 import MP4

from core.driver import trim_resource
from core.streaming_service import YouTubeService, VimeoService


def test_download_youtube_resources_and_combine(tmpdir) -> None:

    service = YouTubeService()

    """
    Test download resources from YouTube, merging the video/audio and trim.
    :return: Nothing
    """
    # BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV
    test_video_id = 'XsX3ATc3FbA'
    test_resolution = '1080p'

    expected_video_stream_path = os.path.join(tmpdir, 'video_stream_1080p.mp4')
    expected_audio_stream_path = os.path.join(tmpdir, 'audio_stream.mp3')

    service.download_video(
        test_video_id,
        test_resolution,
        tmpdir,
        "combined_video.mp4")

    assert exists(expected_video_stream_path)
    video = VideoFileClip(expected_video_stream_path)
    assert int(video.duration) == 252

    assert exists(expected_audio_stream_path)
    audio = MP4(expected_audio_stream_path)
    assert int(audio.info.length) == 252

    combined_path = os.path.join(tmpdir, "combined_video.mp4")
    final_path = os.path.join(tmpdir, "final_video.mp4")

    assert exists(combined_path)
    video = VideoFileClip(combined_path)
    assert int(video.duration) == 252
    assert int(video.audio.duration) == 252

    trim_resource(combined_path, final_path, 60, 120)

    assert exists(final_path)
    video = VideoFileClip(final_path)
    assert int(video.duration) >= 60 or int(video.duration) <= 61
    assert int(video.audio.duration) >= 60 or int(video.duration) <= 61


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
