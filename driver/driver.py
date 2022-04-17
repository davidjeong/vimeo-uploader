"""
This is the script to
1. download the video from YouTube in 1440p/1080p
2. download the audio for video separately
3. merge the audio and video
4. trim the merged video using start and end timestamp
5. upload the video to vimeo with supplied date
6. edit the video thumbnail
"""

import json
import logging
import os
import re
import sys
import time
from datetime import date

import ffmpeg
import pytube
import vimeo
from pytube import YouTube
from pytube.cli import on_progress

from driver.vimeo_configuration import VimeoConfiguration

save_path = os.getcwd() + '\\tmp_videos'
youtube_video_regex = "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

logging.basicConfig(filename='output.log', encoding='utf-8', level=logging.DEBUG)


class Driver:

    def __init__(self, vimeo_config):
        self.vimeo_config = vimeo_config

    def process(self, video_config):
        url = video_config.video_url
        start_time = video_config.start_time_in_sec
        end_time = video_config.end_time_in_sec
        image = video_config.image_url
        resolution = video_config.resolution
        title = video_config.video_title

        # Validate the video url
        validate_video_url(url)
        current_time = round(time.time() * 1000)

        # sanitization
        if title is None:
            today = date.today()
            current_date = today.strftime("%m/%d/%y")
            title = "(CW) {}".format(current_date)

        suffix = str(current_time)
        tmp_video_name = "video_" + suffix + ".mp4"
        tmp_audio_name = "audio_" + suffix + ".mp3"
        tmp_full_path = "full_" + suffix + ".mp4"

        tmp_video_path = get_absolute_path(tmp_video_name)
        tmp_audio_path = get_absolute_path(tmp_audio_name)
        tmp_full_path = get_absolute_path(tmp_full_path)

        download_youtube_resources(url, tmp_video_name, tmp_audio_name, resolution)

        logging.info("Downloaded the video and audio tracks")
        logging.info("Now, going to try to magically merge the video and audio with trim")

        # Call ffmpeg to merge and trim the video.
        join_and_trim(tmp_video_path, tmp_audio_path, tmp_full_path, start_time, end_time)

        # Now we want to authenticate against Vimeo and upload the video with title
        client = vimeo.VimeoClient(
            token=self.vimeo_config.token,
            key=self.vimeo_config.key,
            secret=self.vimeo_config.secret
        )

        logging.info('Uploading video to Vimeo from path: %s' % tmp_full_path)
        try:
            uri = client.upload(tmp_full_path, data={
                'name': title,
                'privacy': {
                    'comments': 'nobody'
                }
            })

            video_data = client.get(uri + '?fields=transcode.status').json()
            logging.info('The transcode status for {} is: {}'.format(uri, video_data['transcode']['status']))

        except vimeo.exceptions.VideoUploadFailure as e:
            # We may have had an error. We can't resolve it here necessarily, so
            # report it to the user.
            logging.error('Error uploading %s' % tmp_full_path)
            logging.error('Server reported: %s' % e.message)
            sys.exit(1)

        # Activate the thumbnail image on video if passed in
        if image:
            client.upload_picture(uri, image, activate=True)

        logging.info(
            "Vimeo URL \"https://vimeo.com/[video_id]\" where the video_id is the number in "
            "the URI\n")
        logging.info("This is the link supplied to the website\n")
        return


def get_seconds(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def get_absolute_path(file_name):
    return "{}\\{}".format(save_path, file_name)


def get_vimeo_configuration(config):
    config = json.load(open(config))
    if 'access_token' not in config:
        raise Exception("access_token is missing from config json")
    if 'client_id' not in config:
        raise Exception("client_id is missing from config json")
    if 'client_secret' not in config:
        raise Exception("client_secret is missing from config json")

    token = config['access_token'],
    key = config['client_id'],
    secret = config['client_secret']
    return VimeoConfiguration(token, key, secret)


def download_youtube_resources(url, video_name, audio_name, resolution):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        video = yt.streams.filter(resolution=resolution).first()
        video.download(save_path, video_name)
        audio = yt.streams.filter(only_audio=True).first()
        audio.download(save_path, audio_name)
    except pytube.exceptions.PytubeError as e:
        print("Failed to download the video or audio " + str(e))
        sys.exit(1)


def validate_video_url(video_url):
    match = re.match(youtube_video_regex, video_url)
    if not match:
        raise Exception("YouTube video URL {}", video_url)


def join_and_trim(video_path, audio_path, output_path, start, end):
    video = ffmpeg.input(video_path).trim(start=start, end=end)
    audio = ffmpeg.input(audio_path).trim(start=start, end=end)
    joined= ffmpeg.concat(video, audio, v=1, a=1).node
    output = ffmpeg.output(joined[0], joined[1], output_path)
    output.run()
