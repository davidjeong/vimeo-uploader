import json
import os

from app import handle_get_video_metadata


def test_handle_get_video_metadata() -> None:
    os.environ['ENV'] = 'development'
    event_object = {
        "queryStringParameters": {
            "platform": "youtube",
            "video_id": "XsX3ATc3FbA"
        }
    }

    response = handle_get_video_metadata(event_object, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["video_id"] == "XsX3ATc3FbA"
    assert body["title"] == "BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV"
    assert body["author"] == "HYBE LABELS"
    assert body["length_in_sec"] == 253
    assert body["publish_date"] == "2019-04-12"
    assert body["resolutions"] == [
        "144p", "240p", "360p", "480p", "720p", "1080p"]
