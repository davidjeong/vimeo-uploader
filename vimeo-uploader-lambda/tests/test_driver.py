import os
from unittest import mock

from core.driver import Driver
from core.generated import model_pb2


def test_get_video_metadata() -> None:
    video_id = "XsX3ATc3FbA"
    title = "BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV"
    author = "HYBE LABELS"
    length_in_sec = 253
    publish_date = "2019-04-12"
    download_platform = mock.MagicMock()
    mock_video_metadata = model_pb2.VideoMetadata(
        video_id=video_id,
        title=title,
        author=author,
        length_in_sec=length_in_sec,
        publish_date=publish_date)
    download_platform.get_video_metadata.return_value = mock_video_metadata
    driver = Driver(download_platform=download_platform)
    video_metadata = driver.get_video_metadata(video_id)
    assert video_metadata.video_id == video_id
    assert video_metadata.title == title
    assert video_metadata.author == author
    assert video_metadata.length_in_sec == length_in_sec
    assert video_metadata.publish_date == publish_date


def test_process_video() -> None:
    video_id = "XsX3ATc3FbA"
    start_time_in_sec = 60
    end_time_in_sec = 120
    image_identifier = ""
    title = "BTS MV"
    download = True
    upload_url = "https://vimeo.com/XsX3ATc3FbA"
    download_url = "https://s3.amazon.com/XsX3ATc3FbA"
    s3_bucket_name = "vimeo-uploader-bucket"
    download_platform = mock.MagicMock()
    download_platform.download_video.return_value = True
    upload_platform = mock.MagicMock()
    upload_platform.upload_video.return_value = upload_url
    s3_client = mock.MagicMock()
    s3_client.generate_presigned_url.return_value = download_url
    os.environ['S3_VIDEO_BUCKET_NAME'] = s3_bucket_name
    driver = Driver(s3_client, download_platform, upload_platform)
    video_process_result = driver.process_video(
        video_id,
        start_time_in_sec,
        end_time_in_sec,
        image_identifier,
        title,
        download)
    download_platform.download_video.assert_called_with(
        video_id,
        start_time_in_sec,
        end_time_in_sec,
        f"/tmp/{video_id}",
        f"{video_id}_{start_time_in_sec}_{end_time_in_sec}.mp4")
    upload_platform.upload_video.assert_called_with(
        f"/tmp/{video_id}/{video_id}_{str(start_time_in_sec)}_{str(end_time_in_sec)}.mp4",
        title,
        None)
    assert video_process_result.download_url == download_url
    assert video_process_result.upload_url == upload_url
