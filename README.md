# Vimeo Uploader
This is a GUI-based application that was originally written as a python script to download videos from Youtube (video specified via url), 
trim the video using two specified start and end timestamps (second granularity), and then re-upload to Vimeo.

Since then, the project has evolved into a full-fledged GUI application using [tkinter](https://docs.python.org/3/library/tkinter.html/) that will
accept user input via text/dropdown and translate that into automated download/upload.

## Pre-requisites
- [ffmpeg](https://ffmpeg.org/)
  -  linux - Use command  ```sudo apt-get install ffmpeg``` or compile from source downloaded from site.
  -  mac - use command ```brew install ffmpeg```
  -  windows - download from site, then add `ffmpeg/bin` to path
- `vimeo_config.bin` which is encrypted binary file containing vimeo API credentials required for automated upload via API

## Program behavior
- Application will download the video/audio streams separately in user documents folder (`Users\<user>\My Documents` in Windows, 
`/Users/<user>/Documents` in Mac)
- Then combine the two streams into a single container (.mp4) file
- Then trim the .mp4 file based on input timestamps
- Then upload the video to vimeo

## How to compile the executable/dmg
- Clone the repository
- Install the pip packages via `pip install -r requirements.txt`
- Run the command ```pyinstaller gui/main.py -n vimeo-uploader```
- Artifact can be accessed in `dist/`