"""
This is the script to
1. download the video from YouTube in 1440p/1080p
2. download the audio for video separately
3. merge the audio and video
4. trim the merged video using start and end timestamp
5. upload the video to vimeo with supplied date
6. edit the video thumbnail
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import date
from os.path import exists

import ffmpeg
import pytube
import vimeo
from pytube import YouTube
from pytube.cli import on_progress

from video_configuration import VideoConfiguration

save_path = os.getcwd() + '\\tmp_videos'
youtube_video_regex = "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

logging.basicConfig(filename='output.log', encoding='utf-8', level=logging.DEBUG)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='URL for YouTube video', required=True)
    parser.add_argument('-s', '--start', help='Start time of video in format 00:00:00', required=True)
    parser.add_argument('-e', '--end', help='End time of video in format 00:00:00', required=True)
    parser.add_argument('-c', '--config', help='Path to the config required by Vimeo', required=True)
    parser.add_argument('-i', '--image', help='Path to the thumbnail image of the video')
    parser.add_argument('-r', '--resolution', help='Resolution of the video', default='1080p')
    parser.add_argument('-t', '--title', help='Title of the video')
    args = parser.parse_args()

    video_config = VideoConfiguration(args.url, args.start, args.end, args.resolution, args.title, args.image)
    logging.info("Downloading video from {} with {} resolution".format(args.url, args.resolution))

    file_exists = exists(args.config)
    if not file_exists:
        logging.error("Failed to find config file at {}", args.config)
        sys.exit(1)

    config = json.load(open(args.config))

    # Validate the video url
    validate_video_url(args.url)
    current_time = round(time.time() * 1000)

    # sanitization
    title = args.title
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

    download_youtube_resources(args.url, tmp_video_name, tmp_audio_name, args.resolution)

    logging.info("Downloaded the video and audio tracks")
    logging.info("Now, going to try to magically merge the video and audio with trim")

    # Call ffmpeg to merge and trim the video.
    video = ffmpeg.input(tmp_video_path)
    audio = ffmpeg.input(tmp_audio_path)
    output = ffmpeg.output(video, audio, tmp_full_path, vcodec='copy', acodec='aac')
    output.run()

    # Now we want to authenticate against Vimeo and upload the video with title
    client = vimeo.VimeoClient(
        token=config['access_token'],
        key=config['client_id'],
        secret=config['client_secret']
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
    if args.image:
        client.upload_picture(uri, args.image, activate=True)

    logging.info(
        "Vimeo URL \"https://vimeo.com/[video_id]\" where the video_id is the number in "
        "the URI\n")
    logging.info("This is the link supplied to the website\n")


def get_absolute_path(file_name):
    return "{}\\{}".format(save_path, file_name)


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
        raise Exception("YouTube video URL {}")


if __name__ == "__main__":
    main()
