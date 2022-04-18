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
import re
import sys
import tempfile
import time
from datetime import date

import ffmpeg
import pytube
import vimeo
from pytube import YouTube
from pytube.cli import on_progress

from config.video_configuration import VideoConfiguration
from config.vimeo_configuration import VimeoConfiguration
from core.util import get_absolute_path, get_vimeo_configuration, get_video_configuration

save_path = tempfile.gettempdir()
youtube_video_regex = "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

logging.basicConfig(filename='output.log', encoding='utf-8', level=logging.DEBUG)


class Driver:

    def __init__(self, vimeo_config: VimeoConfiguration) -> None:
        self.vimeo_config = vimeo_config

    def update_vimeo_config(self, vimeo_config: VimeoConfiguration) -> None:
        self.vimeo_config = vimeo_config

    def process(self, video_config: VideoConfiguration) -> None:
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
        if title is None or not title:
            today = date.today()
            current_date = today.strftime("%m/%d/%y")
            title = "(CW) {}".format(current_date)

        suffix = str(current_time)
        tmp_video_name = "video_" + suffix + ".mp4"
        tmp_audio_name = "audio_" + suffix + ".mp3"
        tmp_combined_name = "combined_" + suffix + ".mp4"
        tmp_final_name = "final_" + suffix + ".mp4"

        tmp_video_path = get_absolute_path(save_path, tmp_video_name)
        tmp_audio_path = get_absolute_path(save_path, tmp_audio_name)
        tmp_combined_path = get_absolute_path(save_path, tmp_combined_name)
        tmp_final_path = get_absolute_path(save_path, tmp_final_name)

        download_youtube_resources(url, tmp_video_name, tmp_audio_name, resolution)

        logging.info("Downloaded the video and audio tracks")
        logging.info("Now, going to try to magically merge the video and audio with trim")

        # Call ffmpeg to merge.
        join_resource(tmp_video_path, tmp_audio_path, tmp_combined_path)
        # Call ffmpeg to trim.
        trim_resource(tmp_combined_path, tmp_final_path, start_time, end_time)

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


def download_youtube_resources(url: str, video_name: str, audio_name: str, resolution: str) -> None:
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        video = yt.streams.filter(resolution=resolution).first()
        video.download(save_path, video_name)
        audio = yt.streams.filter(only_audio=True).first()
        audio.download(save_path, audio_name)
    except pytube.exceptions.PytubeError as e:
        print("Failed to download the video or audio " + str(e))
        raise e


def validate_video_url(video_url: str) -> None:
    match = re.match(youtube_video_regex, video_url)
    if not match:
        raise Exception("YouTube video URL {}", video_url)


def join_resource(video_path: str, audio_path: str, output_path: str) -> None:
    video = ffmpeg.input(video_path)
    audio = ffmpeg.input(audio_path)
    output = ffmpeg.output(video, audio, output_path, vcodec='copy', acodec='aac')
    output.run()


def trim_resource(input_path: str, output_path: str, start_time: str, end_time: str) -> None:
    input_stream = ffmpeg.input(input_path)
    video = (
        input_stream.video.trim(start=start_time, end=end_time).setpts('PTS-STARTPTS')
    )
    audio = (
        input_stream.audio.filter_('atrim', start=start_time, end=end_time).filter_('asetpts', 'PTS-STARTPTS')
    )
    joined = ffmpeg.concat(video, audio, v=1, a=1).node
    output = ffmpeg.output(joined[0], joined[1], output_path)
    output.run()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='URL for YouTube video', required=True)
    parser.add_argument('-s', '--start', help='Start time of video in format 00:00:00', required=True)
    parser.add_argument('-e', '--end', help='End time of video in format 00:00:00', required=True)
    parser.add_argument('-c', '--config', help='Path to the config required by Vimeo', required=True)
    parser.add_argument('-i', '--image', help='Path to the thumbnail image of the video')
    parser.add_argument('-r', '--resolution', help='Resolution of the video', default='1080p')
    parser.add_argument('-t', '--title', help='Title of the video')
    args = parser.parse_args()

    config = json.load(open(args.config))
    vimeo_config = get_vimeo_configuration(config)
    video_config = get_video_configuration(args.url, args.start, args.end, args.resolution, args.title, args.image)

    driver = Driver(vimeo_config)
    driver.process(video_config)


if __name__ == "__main__":
    main()
