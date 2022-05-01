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
import logging
import os.path
import sys
from datetime import date

import pytube
import vimeo
from moviepy.video.io.ffmpeg_tools import ffmpeg_merge_video_audio, ffmpeg_extract_subclip
from pytube import YouTube
from pytube.cli import on_progress


from core.util import get_vimeo_configuration, get_video_configuration, get_youtube_url
from model.config import VimeoConfiguration, AppDirectoryConfiguration, VideoConfiguration

youtube_video_regex = "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

logging.basicConfig(filename='output.log', encoding='utf-8', level=logging.DEBUG)


class Driver:

    def __init__(self, vimeo_config: VimeoConfiguration, app_directory_config: AppDirectoryConfiguration) -> None:
        self.vimeo_config = vimeo_config
        self.app_directory_config = app_directory_config

    def update_vimeo_config(self, vimeo_config: VimeoConfiguration) -> None:
        self.vimeo_config = vimeo_config

    def update_app_directory_config(self, app_directory_config: AppDirectoryConfiguration) -> None:
        self.app_directory_config = app_directory_config

    def process(self, video_config: VideoConfiguration) -> None:
        video_id = video_config.video_id
        start_time_in_sec = video_config.start_time_in_sec
        end_time_in_sec = video_config.end_time_in_sec
        image = video_config.image_url
        resolution = video_config.resolution
        title = video_config.video_title

        # sanitization
        if title is None or not title:
            today = date.today()
            current_date = today.strftime("%m/%d/%y")
            title = "(CW) {}".format(current_date)

        url = get_youtube_url(video_id)
        suffix = f'{str(video_config.start_time_in_sec)}_{str(video_config.end_time_in_sec)}'
        video_stream_name = f"video_stream_{resolution}.mp4"
        audio_stream_name = f"audio_stream_{resolution}.mp3"
        combined_video_name = f"combined_{resolution}.mp4"
        trimmed_video_name = f"{suffix}_{resolution}.mp4"

        video_dir = os.path.join(self.app_directory_config.videos_dir, video_id)
        if not os.path.exists(video_dir):
            logging.info("Creating directory " + video_dir)
            os.mkdir(video_dir)
        video_stream_path = os.path.join(video_dir, video_stream_name)
        audio_stream_path = os.path.join(video_dir, audio_stream_name)
        combined_video_path = os.path.join(video_dir, combined_video_name)
        trimmed_video_path = os.path.join(video_dir, trimmed_video_name)

        if not os.path.exists(video_stream_path) or not os.path.exists(audio_stream_path):
            download_youtube_resources(video_dir, url, video_stream_name, audio_stream_name, resolution)
            logging.info("Downloaded the video and audio tracks")

        logging.info("Now, going to try to magically merge the video and audio with trim")

        # Call ffmpeg to merge.
        if not os.path.exists(combined_video_path):
            join_resource(video_stream_path, audio_stream_path, combined_video_path)
            logging.info("Finished joining the video")

        # Call ffmpeg to trim.
        if not os.path.exists(trimmed_video_path):
            trim_resource(combined_video_path, trimmed_video_path, start_time_in_sec, end_time_in_sec)
            logging.info("Finished trimming the video")

        # Now we want to authenticate against Vimeo and upload the video with title
        client = vimeo.VimeoClient(
            token=self.vimeo_config.token,
            key=self.vimeo_config.key,
            secret=self.vimeo_config.secret
        )

        logging.info('Uploading video to Vimeo from path: %s' % trimmed_video_path)
        uri = upload_video_to_vimeo(client, trimmed_video_path, title)

        # Activate the thumbnail image on video if passed in
        if uri is not None and image:
            client.upload_picture(uri, image, activate=True)

        logging.info(
            "Vimeo URL \"https://vimeo.com/[video_id]\" where the video_id is the number in "
            "the URI\n")
        logging.info("This is the link supplied to the website\n")
        return


def download_youtube_resources(download_path: str, url: str, video_name: str, audio_name: str, resolution: str) -> None:
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        video = yt.streams.filter(resolution=resolution).first()
        video.download(download_path, video_name)
        audio = yt.streams.filter(only_audio=True).first()
        audio.download(download_path, audio_name)
    except pytube.exceptions.PytubeError as e:
        print("Failed to download the video or audio " + str(e))
        raise e


def join_resource(video_path: str, audio_path: str, output_path: str) -> None:
    ffmpeg_merge_video_audio(video_path, audio_path, output_path)


def trim_resource(input_path: str, output_path: str, start_time_in_sec: int, end_time_in_sec: int) -> None:
    ffmpeg_extract_subclip(input_path, start_time_in_sec, end_time_in_sec, output_path)


def upload_video_to_vimeo(client: vimeo.VimeoClient, video_path: str, video_title: str) -> str:
    """
    Try to upload the video to vimeo using vimeo client.
    :param client: client to upload the video with
    :param video_path: path to the video
    :param video_title: title of the video
    :return: URI if successful, otherwise None
    """

    try:
        uri = client.upload(video_path, data={
            'name': video_title,
            'privacy': {
                'comments': 'nobody'
            }
        })
    except vimeo.exceptions.VideoUploadFailure as e:
        # We may have had an error. We can't resolve it here necessarily, so
        # report it to the user.
        logging.error('Error uploading %s' % video_path)
        logging.error('Server reported: %s' % e.message)
        raise e

    video_data = client.get(uri + '?fields=transcode.status').json()
    logging.info('The transcode status for {} is: {}'.format(uri, video_data['transcode']['status']))
    return uri


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

    vimeo_config = get_vimeo_configuration(args.config)

    try:
        video_config = get_video_configuration(args.url, args.start, args.end, args.resolution, args.title, args.image)
    except Exception as e:
        logging.error("Failed with exception " % e)
        sys.exit(1)

    driver = Driver(vimeo_config)
    driver.process(video_config)


if __name__ == "__main__":
    main()
