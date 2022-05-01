import logging
import os
from os.path import exists

import yaml

from config.video_configuration import VideoConfiguration
from config.vimeo_configuration import VimeoConfiguration
from core.exceptions import VimeoConfigurationException

url_prefix = 'https://www.youtube.com/watch?v='


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
        raise ValueError('Failed to split timestamp %s' % time_str)
    return int(h) * 3600 + int(m) * 60 + int(s)


def get_absolute_path(save_path: str, file_name: str) -> str:
    return os.path.join(save_path, file_name)


def get_youtube_url(video_id: str) -> str:
    return url_prefix + video_id


def get_vimeo_configuration(config_path: str) -> VimeoConfiguration:
    file_exists = exists(config_path)
    if not file_exists:
        raise Exception("Config file does not exist at %s", config_path)

    with open(config_path, 'r') as file:
        config_yaml = yaml.safe_load(file)
        if 'access_token' not in config_yaml:
            raise VimeoConfigurationException("access_token is missing from config yaml")
        if 'client_id' not in config_yaml:
            raise VimeoConfigurationException("client_id is missing from config yaml")
        if 'client_secret' not in config_yaml:
            raise VimeoConfigurationException("client_secret is missing from config yaml")

    token = config_yaml['access_token']
    key = config_yaml['client_id']
    secret = config_yaml['client_secret']
    return VimeoConfiguration(token, key, secret)


def get_video_configuration(video_url: str, start_time: str, end_time: str, resolution: str, video_title: str,
                            image_url: str) -> VideoConfiguration:
    start_time_in_sec = get_seconds(start_time)
    end_time_in_sec = get_seconds(end_time)
    return VideoConfiguration(video_url, start_time_in_sec, end_time_in_sec, resolution, video_title, image_url)
