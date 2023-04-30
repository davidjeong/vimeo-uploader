> :warning: **This is no longer being maintained**

# Vimeo Uploader Python Client
This is a python-based GUI application that communicates with AWS Lambda (see [Vimeo Uploader Lambda](https://github.com/davidjeong/vimeo-uploader/tree/main/vimeo-uploader-lambda)) 
Users will be able to specify YouTube video URL, trim timestamps, and other information. It uses python GUI framework [tkinter](https://docs.python.org/3/library/tkinter.html/).

## Pre-requisites
- Installation of Python 3.9+ (_might_ require Python 3.11)
- `credentials.yaml` which contains AWS credentials.
  e.g.
  ```
  aws_access_key_id: foo
  aws_secret_access_key: bar
  ```
- Location of this file depends on the operating system.
  - On Windows, this goes under `C:\Users\<user_name>\My Documents\Vimeo Uploader`
  - On Mac, this goes under `Users/<user_name>/Documents/Vimeo Uploader`

## How to compile the executable/dmg
- Clone the repository
- Install the pip packages via `pip install -r requirements.txt`
- Run the command for installation.
  - On Windows, the command is ```pyinstaller gui/main.py -n vimeo-uploader```
  - On Mac, the command is ```pyinstaller --onedir --windowed gui/main.py -n vimeo-uploader```
- Artifact can be accessed in `dist/`

> NOTE: Currently the installer might not work as intended, and the only way to start the application may be via IntelliJ.
