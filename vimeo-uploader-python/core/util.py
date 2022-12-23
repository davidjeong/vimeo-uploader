"""
Utility model used by application
"""

import logging


def get_seconds(time_str: str) -> int:
    """
    Get seconds from timestamp string.
    :param time_str: Time string in format hh:mm:ss
    :return: timestamp in seconds
    """
    try:
        hour, minute, second = time_str.split(':')
    except ValueError as error:
        logging.error("Failed to split the timestamp string by delimiter ':'")
        raise ValueError from error
    return int(hour) * 3600 + int(minute) * 60 + int(second)
