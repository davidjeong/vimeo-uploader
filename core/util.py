"""
Utility model used by application
"""

import logging
import os
from os.path import exists

import yaml

from model.config import VimeoConfiguration, VideoConfiguration
from model.exception import VimeoConfigurationException

YOUTUBE_URL_PREFIX = 'https://www.youtube.com/watch?v='


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


def get_absolute_path(save_path: str, file_name: str) -> str:
    """
    Get absolute path of file
    :param save_path:
    :param file_name:
    :return:
    """
    return os.path.join(save_path, file_name)


def get_youtube_url(video_id: str) -> str:
    """
    Get the absolute YouTube url
    :param video_id:
    :return:
    """
    return YOUTUBE_URL_PREFIX + video_id


def get_vimeo_configuration(config_path: str) -> VimeoConfiguration:
    """
    Get the vimeo configuration from config path
    :param config_path:
    :return:
    """
    file_exists = exists(config_path)
    if not file_exists:
        raise VimeoConfigurationException(
            f"Config file does not exist at {config_path}")

    with open(config_path, 'r', encoding="utf8") as file:
        config_yaml = yaml.safe_load(file)
        if 'access_token' not in config_yaml:
            raise VimeoConfigurationException(
                "access_token is missing from config yaml")
        if 'client_id' not in config_yaml:
            raise VimeoConfigurationException(
                "client_id is missing from config yaml")
        if 'client_secret' not in config_yaml:
            raise VimeoConfigurationException(
                "client_secret is missing from config yaml")

    token = config_yaml['access_token']
    key = config_yaml['client_id']
    secret = config_yaml['client_secret']
    return VimeoConfiguration(token, key, secret)


def get_video_configuration(
        video_url: str,
        start_time: str,
        end_time: str,
        resolution: str,
        video_title: str,
        image_url: str) -> VideoConfiguration:
    """
    Get video configuration from input values
    :param video_url:
    :param start_time:
    :param end_time:
    :param resolution:
    :param video_title:
    :param image_url:
    :return:
    """
    start_time_in_sec = get_seconds(start_time)
    end_time_in_sec = get_seconds(end_time)
    return VideoConfiguration(
        video_url,
        start_time_in_sec,
        end_time_in_sec,
        resolution,
        video_title,
        image_url)
