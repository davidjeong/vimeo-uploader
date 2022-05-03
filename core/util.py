"""
Utility model used by application
"""

import logging
from os.path import exists

import yaml

from model.config import VimeoClientConfiguration, VideoConfiguration
from model.exception import VimeoClientConfigurationException, UnsetConfigurationException


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


def get_vimeo_client_configuration(
        config_path: str) -> VimeoClientConfiguration:
    """
    Get the vimeo configuration from config path
    :param config_path:
    :return:
    """
    file_exists = exists(config_path)
    if not file_exists:
        raise UnsetConfigurationException(
            f"Config file does not exist at {config_path}")

    with open(config_path, 'r', encoding="utf8") as file:
        config_yaml = yaml.safe_load(file)
        if 'access_token' not in config_yaml:
            raise VimeoClientConfigurationException(
                "access_token is missing from config yaml")
        if 'client_id' not in config_yaml:
            raise VimeoClientConfigurationException(
                "client_id is missing from config yaml")
        if 'client_secret' not in config_yaml:
            raise VimeoClientConfigurationException(
                "client_secret is missing from config yaml")

    token = config_yaml['access_token']
    key = config_yaml['client_id']
    secret = config_yaml['client_secret']
    return VimeoClientConfiguration(token, key, secret)


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
