import json
import os
import tempfile

import pytest

from core.util import get_absolute_path, get_vimeo_configuration


def test_get_absolute_path() -> None:
    """
    def get_absolute_path(save_path: str, file_name: str) -> str:
    return "{}\\{}".format(save_path, file_name)
    :return:
    """
    save_path = "\\Users\\foo\\Documents"
    file_name = "bar.xyz"
    absolute_path = get_absolute_path(save_path, file_name)
    assert absolute_path == "\\Users\\foo\\Documents\\bar.xyz"


def test_get_vimeo_configuration(tmpdir) -> None:
    with pytest.raises(Exception, match="config file does not exist"):
        invalid_path = "foo/bar"
        get_vimeo_configuration(invalid_path)

    sample_config = {
        "access_token": "foo",
        "client_id": "bar",
        "client_secret": "baz"
    }

    with open(os.path.join(tmpdir, "tmp.json"), "w") as tmp:
        tmp.write(json.dumps(sample_config))
        tmp.flush()
        vimeo_config = get_vimeo_configuration(tmp.name)
        assert vimeo_config.token == 'foo'
        assert vimeo_config.key == 'bar'
        assert vimeo_config.secret == 'baz'
