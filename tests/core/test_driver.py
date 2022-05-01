from os.path import exists
from unittest import mock

from moviepy.video.io.VideoFileClip import VideoFileClip
from mutagen.mp4 import MP4

from core.driver import download_youtube_resources, join_resource, trim_resource, upload_video_to_vimeo
from core.util import get_absolute_path


def test_download_youtube_resources_and_combine(tmpdir) -> None:
    """
    Test download resources from YouTube, merging the video/audio and trim.
    :return: Nothing
    """
    # BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV
    test_url = 'https://www.youtube.com/watch?v=XsX3ATc3FbA'
    test_resolution = '1080p'

    tmp_video_path = get_absolute_path(tmpdir, 'v.mp4')
    tmp_audio_path = get_absolute_path(tmpdir, 'a.mp3')

    download_youtube_resources(tmpdir, test_url, tmp_video_path, tmp_audio_path, test_resolution)

    assert exists(tmp_video_path)
    video = VideoFileClip(tmp_video_path)
    assert int(video.duration) == 252

    assert exists(tmp_audio_path)
    audio = MP4(tmp_audio_path)
    assert int(audio.info.length) == 252

    combined_path = get_absolute_path(tmpdir, "c.mp4")
    final_path = get_absolute_path(tmpdir, "f.mp4")
    join_resource(tmp_video_path, tmp_audio_path, combined_path)

    assert exists(combined_path)
    video = VideoFileClip(combined_path)
    assert int(video.duration) == 252
    assert int(video.audio.duration) == 252

    trim_resource(combined_path, final_path, 60, 120)

    assert exists(final_path)
    video = VideoFileClip(final_path)
    assert int(video.duration) >= 60 or int(video.duration) <= 61
    assert int(video.audio.duration) >= 60 or int(video.duration) <= 61

    print("Final video in " + final_path)


def test_upload_video_to_vimeo() -> None:
    """
    Test uploading video to vimeo using mock client
    :return: Nothing
    """
    video_path = "/path/to/video"
    video_title = "new title"
    client = mock.MagicMock()
    upload_video_to_vimeo(client, video_path, video_title)
    data_json = {
        'name': video_title,
        'privacy': {
            'comments': 'nobody'
        }
    }
    client.upload.assert_called_with(video_path, data=data_json)
