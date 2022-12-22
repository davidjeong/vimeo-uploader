from app import handle_get_video_metadata
from core.generated import model_pb2
from google.protobuf.json_format import Parse


def test_handle_get_video_metadata() -> None:
    event_object = {
        "queryStringParameters": {
            "platform": "youtube",
            "video_id": "XsX3ATc3FbA"
        }
    }

    response = handle_get_video_metadata(event_object, None)
    assert response["statusCode"] == 200
    print(response["body"])
    video_metadata = Parse(response["body"], model_pb2.VideoMetadata())
    assert video_metadata.video_id == "XsX3ATc3FbA"
    assert video_metadata.title == "BTS (방탄소년단) '작은 것들을 위한 시 (Boy With Luv) (feat. Halsey)' Official MV"
    assert video_metadata.author == "HYBE LABELS"
    assert video_metadata.length_in_sec == 253
    assert video_metadata.publish_date == "2019-04-12"
    assert video_metadata.resolutions == [
        "144p", "240p", "360p", "480p", "720p", "1080p"]
