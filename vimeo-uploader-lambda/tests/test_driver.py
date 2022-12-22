import base64
import os

from core.driver import Driver


def test_write_base64_image_content_to_disk(tmpdir):
    os.environ['ENV'] = 'development'
    test_image_path = os.path.join('tests', 'resources', 'thumbnail.jpg')
    with open(test_image_path, 'rb') as file:
        encoded_string = base64.b64encode(file.read())
    driver = Driver()
    written_path = driver._write_image_stream_to_file(
        encoded_string, tmpdir, "thumbnail.jpg")
    assert os.path.getsize(test_image_path) == os.path.getsize(written_path)
