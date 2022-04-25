import json
import logging
from os.path import exists

from config.video_configuration import VideoConfiguration
from config.vimeo_configuration import VimeoConfiguration


def get_seconds(time_str: str) -> int:
    """
    Get seconds from timestamp string.
    :param time_str: Time string in format hh:mm:ss
    :return: timestamp in seconds
    """
    try:
        h, m, s = time_str.split(':')
    except ValueError:
        logging.error("Failed to split the timestamp string by delimiter ':'")
        raise ValueError('Failed to split timestamp ' % time_str)
    return int(h) * 3600 + int(m) * 60 + int(s)


def get_absolute_path(save_path: str, file_name: str) -> str:
    return "{}\\{}".format(save_path, file_name)


def get_vimeo_configuration(config: str) -> VimeoConfiguration:
    file_exists = exists(config)
    if not file_exists:
        raise Exception("config file does not exist")

    config = json.load(open(config))
    if 'access_token' not in config:
        raise Exception("access_token is missing from config json")
    if 'client_id' not in config:
        raise Exception("client_id is missing from config json")
    if 'client_secret' not in config:
        raise Exception("client_secret is missing from config json")

    token = config['access_token']
    key = config['client_id']
    secret = config['client_secret']
    return VimeoConfiguration(token, key, secret)


def get_video_configuration(video_url: str, start_time: str, end_time: str, resolution: str, video_title: str,
                            image_url: str) -> VideoConfiguration:
    try:
        start_time_in_sec = get_seconds(start_time)
        end_time_in_sec = get_seconds(end_time)
    except ValueError as e:
        raise Exception(e)
    return VideoConfiguration(video_url, start_time_in_sec, end_time_in_sec, resolution, video_title, image_url)
