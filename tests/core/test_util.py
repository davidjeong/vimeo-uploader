import json
import os

import pytest

from core.util import get_vimeo_client_configuration, get_seconds


def test_get_seconds() -> None:
    initial_time = '00:00:00'
    initial_time_in_sec = get_seconds(initial_time)
    assert initial_time_in_sec == 0

    half_hour_time = '00:30:00'
    half_hour_time_in_sec = get_seconds(half_hour_time)
    assert half_hour_time_in_sec == 60 * 30

    hour_time = '01:00:00'
    hour_time_in_sec = get_seconds(hour_time)
    assert hour_time_in_sec == 60 * 60

    hour_time_and_one_second = '01:00:01'
    hour_time_and_one_second_in_sec = get_seconds(hour_time_and_one_second)
    assert hour_time_and_one_second_in_sec == 60 * 60 + 1


def test_get_vimeo_configuration(tmpdir) -> None:
    with pytest.raises(Exception, match="Config file does not exist"):
        invalid_path = "foo/bar"
        get_vimeo_client_configuration(invalid_path)

    sample_config = {
        "access_token": "foo",
        "client_id": "bar",
        "client_secret": "baz"
    }

    with open(os.path.join(tmpdir, "tmp.json"), "w") as tmp:
        tmp.write(json.dumps(sample_config))
        tmp.flush()
        vimeo_config = get_vimeo_client_configuration(tmp.name)
        assert vimeo_config.token == 'foo'
        assert vimeo_config.key == 'bar'
        assert vimeo_config.secret == 'baz'
