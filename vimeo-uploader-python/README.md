# Vimeo Uploader
This is a GUI-based application that downloads videos from YouTube (video specified via url), 
trim the video using two specified start and end timestamps (second granularity), and then re-upload to Vimeo.

It uses GUI framework [tkinter](https://docs.python.org/3/library/tkinter.html/).
The workflow it accepts user input via text/dropdown and passes the parameters to AWS Lambda functions.

## Pre-requisites
- `credentials.yaml` which contains AWS credentials.

## How to compile the executable/dmg
- Clone the repository
- Install the pip packages via `pip install -r requirements.txt`
- Run the command ```pyinstaller gui/main.py -n vimeo-uploader```
  - On Mac, the command is ```pyinstaller --onedir --windowed gui/main.py -n vimeo-uploader```
- Artifact can be accessed in `dist/`