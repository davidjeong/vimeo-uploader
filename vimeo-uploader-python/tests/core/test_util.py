from core.util import get_seconds


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
