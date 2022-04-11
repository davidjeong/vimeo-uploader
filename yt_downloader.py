'''
This is the script to 
1. download the video from youtube in 1440p/1080p
2. download the audio for video separately
3. merge the audio and video
4. trim the merged video using start and end timestamp
5. upload the video to vimeo with supplied date
6. edit the video thumbnail
'''

import argparse
from datetime import date
import json
import os
from pytube import YouTube
from pytube.cli import on_progress
import sys
import vimeo

save_path = os.getcwd() + '/videos'
config_file = os.path.dirname(os.path.realpath(__file__)) + '/config.json'
config = json.load(open(config_file))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='URL for the video (part after v=)', required=True)
    parser.add_argument('-s', '--start', help='Start time of video in format 00:00:00', required=True)
    parser.add_argument('-e', '--end', help='End time of video in format 00:00:00', required=True)
    parser.add_argument('-i', '--image', help='Path to the thumbnail image of the video', required=True) 
    parser.add_argument('-d', '--date', help='Date of the sermon video in format mm/dd/yy', required=False)
    parser.add_argument('-uf', '--url-fix', help='Set to true if url start with \'-\', false by default', required=False)
    args = parser.parse_args()

    url = args.url
    start_time = args.start
    end_time = args.end
    sermon_date = args.date
    image_path = args.image
    # Input sanitization
    if sermon_date is None:
        sermon_date = date.today().strftime('%m/%d/%y')
    if not os.path.exists(image_path):
        print("File {} does not exist. Please check path to thumbnail image.".format(image_path))
        sys.exit(1)

    print("Downloading video from https://www.youtube.com/watch?v={} with highest resolution".format(url))

    try:
        full_url = "https://www.youtube.com/watch?v={}".format(url)
        yt = YouTube(full_url, on_progress_callback = on_progress)
    except:
        print("Connection error trying to get the video")
        sys.exit(1)
    print("Found video with title \"{}\"".format(yt.title))
    try:
        video = yt.streams.filter(resolution = '1080p').first()
        video.download(save_path, "video.mp4")
        print("Video downloaded successfully!\n")
    except Exception as e:
        print("Failed to download the video" + str(e))
        sys.exit(1)
    try:
        audio = yt.streams.filter(only_audio = True).first()
        audio.download(save_path, "audio.mp3")
        print("Audio downloaded successfully!\n")
    except:
        print("Failed to download the audio")
        sys.exit(1)

    print("Now, going to try to magically merge the video and audio with trim")

    # Call local instance of ffmpeg to merge and trim the video.
    command = "ffmpeg -ss {} -to {} -i {} -ss {} -to {} -i {} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 {}".format(start_time, end_time, video_path, start_time, end_time, audio_path, combined_path)
    os.system(command)

    # Now we want to authenticate against Vimeo and upload the video with title
    client = vimeo.VimeoClient(
        token=config['access_token'],
        key=config['client_id'],
        secret=config['client_secret']
    )

    print('Uploading: %s' % combined_path)

    try:
        uri = client.upload(combined_path, data={
            'name': "(CW) {}".format(sermon_date),
            'privacy': {
                'comments': 'nobody'
            }
        })

        video_data = client.get(uri + '?fields=transcode.status').json()
        print('The transcode status for {} is: {}'.format(uri, video_data['transcode']['status']))
        print('Sermon video uri for date https://{} is : {}'.format(sermon_date, uri))

    except vimeo.exceptions.VideoUploadFailure as e:
        # We may have had an error. We can't resolve it here necessarily, so
        # report it to the user.
        print('Error uploading %s' % combined_path)
        print('Server reported: %s' % e.message)
        sys.exit(1)
    
    # Activate the thumbnail image on video
    client.upload_picture(uri, image_path, activate=True)
    
    print("Now grab the URI, then put the full URL \"https://vimeo.com/[video_id]\" where the video_id is the number in the URI\n")
    print("This is the link supplied to the website\n")

    sys.exit(0)

def get_absolute_path(file_name):
    return "{}\\{}".format(save_path, file_name)

video_path = get_absolute_path("video.mp4")
audio_path = get_absolute_path("audio.mp3")
combined_path = get_absolute_path("combined.mp4")

if __name__ == "__main__":
    main()
