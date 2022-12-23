# Vimeo Uploader
This is a GUI-based application that downloads videos from YouTube (video specified via url), 
trim the video using two specified start and end timestamps (second granularity), and then re-upload to Vimeo.

It uses GUI framework [tkinter](https://docs.python.org/3/library/tkinter.html/).
The workflow it accepts user input via text/dropdown and translate that into a request for backend processes.

## Pre-requisites
- AWS client-side keys for communicating with backend services

## Program behavior
- Application will take inputs via GUI, then pass those via parameters to backend AWS Lambda function.

## How to compile the executable/dmg
- Clone the repository
- Install the pip packages via `pip install -r requirements.txt`
- Run the command ```pyinstaller gui/main.py -n vimeo-uploader```
  - On Mac, the command is ```pyinstaller --onedir --windowed gui/main.py -n vimeo-uploader```
- Artifact can be accessed in `dist/`