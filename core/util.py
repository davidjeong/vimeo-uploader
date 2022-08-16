"""
Utility model used by application
"""

import logging
from os.path import exists

import yaml
from cryptography.fernet import Fernet

from model.config import VimeoClientConfiguration, VideoTrimUploadConfiguration
from model.exception import VimeoClientConfigurationException, UnsetConfigurationException


FERNET_KEY = b'Km4yTNxHkrj3PXsnB0PnbTqpU79CWk0JUbTI8GlqNYQ='


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

    # ideally this should reside in AWS secret manager
    fernet = Fernet(FERNET_KEY)

    def _decrypt_binary() -> bytes:
        """
        Decrypt the config binary
        :return: Decrypt the config binary
        """
        with open(config_path, 'rb') as encrypted_file:
            encrypted = encrypted_file.read()
        return fernet.decrypt(encrypted)

    """
    Get the vimeo configuration from config path
    :param config_path:
    :return:
    """
    file_exists = exists(config_path)
    if not file_exists:
        raise UnsetConfigurationException(
            f"Config file does not exist at {config_path}")

    binary = _decrypt_binary()
    config_yaml = yaml.safe_load(binary)
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


def get_video_trim_upload_configuration(
        video_id: str,
        video_path: str,
        start_time: str,
        end_time: str,
        video_title: str,
        image_url: str) -> VideoTrimUploadConfiguration:
    """
    Get video trim upload configuration from input values
    :param video_id
    :param video_path:
    :param start_time:
    :param end_time:
    :param video_title:
    :param image_url:
    :return:
    """
    start_time_in_sec = get_seconds(start_time)
    end_time_in_sec = get_seconds(end_time)
    return VideoTrimUploadConfiguration(
        video_id,
        video_path,
        start_time_in_sec,
        end_time_in_sec,
        video_title,
        image_url
    )
