import tempfile
from os.path import exists

import pytest
from moviepy.video.io.VideoFileClip import VideoFileClip
from mutagen.mp4 import MP4

from core.driver import download_youtube_resources, join_resource, trim_resource
from core.util import get_absolute_path


@pytest.mark.order1
def test_download_youtube_resources_and_combine(tmpdir) -> None:
    """
    Download resources from YouTube
    :return: Nothing
    """
    # BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV
    test_url = 'https://www.youtube.com/watch?v=XsX3ATc3FbA'
    test_resolution = '1080p'

    save_path = tmpdir
    tmp_video_path = get_absolute_path(save_path, 'v.mp4')
    tmp_audio_path = get_absolute_path(save_path, 'a.mp3')

    download_youtube_resources(test_url, tmp_video_path, tmp_audio_path, test_resolution)

    assert exists(tmp_video_path)
    video = VideoFileClip(tmp_video_path)
    assert int(video.duration) == 252

    assert exists(tmp_audio_path)
    audio = MP4(tmp_audio_path)
    assert int(audio.info.length) == 252

    combined_path = get_absolute_path(save_path, "c.mp4")
    final_path = get_absolute_path(save_path, "f.mp4")
    join_resource(tmp_video_path, tmp_audio_path, combined_path)

    assert exists(combined_path)
    video = VideoFileClip(combined_path)
    assert int(video.duration) == 252
    assert int(video.audio.duration) == 252

    trim_resource(combined_path, final_path, '00:01:00', '00:02:00')

    assert exists(final_path)
    video = VideoFileClip(final_path)
    assert int(video.duration) == 60
    assert int(video.audio.duration) == 60

    print("Final video in " + final_path)
