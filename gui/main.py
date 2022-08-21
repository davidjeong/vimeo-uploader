"""
Main entry for GUI
"""

import logging
import os.path
import platform
import shutil
import subprocess
import sys
import threading
import webbrowser
from dataclasses import dataclass
from tkinter import Tk, Menu, StringVar, messagebox, LEFT, W, filedialog, Button, ttk, BooleanVar, Frame, Toplevel, \
    BOTTOM, X

import vimeo
from pytube.exceptions import RegexMatchError, VideoUnavailable

from core.driver import Driver
from core.streaming_service import SupportedServices
from core.util import get_vimeo_client_configuration, get_video_trim_upload_configuration
from model.config import AppDirectoryConfiguration, VideoDownloadConfiguration
from model.exception import VimeoClientConfigurationException, UnsetConfigurationException

EMPTY_RESOLUTION = ['N/A']
APP_DIRECTORY_NAME = "Vimeo Uploader"


def _about() -> None:
    messagebox.showinfo(
        'About',
        'This is a python-based application to download videos from supported streaming services, trim them, '
        'and re-upload to supported streaming services.')


@dataclass
class ThumbnailHandler:
    """
    Data class for thumbnail path
    """
    thumbnail_path: str = None


class PostDownloadProcessor:

    def __init__(self, video_path: str):
        # Initialize the thumbnail handler
        self.thumbnail_handler = ThumbnailHandler()

        # Get video_id and resolution from outer scope
        self.video_id = video_id_str.get()
        self.resolution = resolution.get()

        # Declare trim/upload specific variables
        self.video_path = video_path
        self.start_time = StringVar()
        self.end_time = StringVar()
        self.image_text = StringVar()
        self.title = StringVar()

        # Create overlay panel
        overlay = Toplevel(root)
        overlay.title(
            f"Overlay for Video ID - {self.video_id} @ [{self.resolution}]")
        frame = Frame(overlay)
        frame.pack(side=BOTTOM, fill=X)

        self.start_label = ttk.Label(
            frame,
            text='Start time of video in format 00:00:00',
            font=(
                'Helvetica',
                10),
            justify=LEFT)
        self.start_entry = ttk.Entry(
            frame,
            textvariable=self.start_time,
            font=(
                'Helvetica',
                10),
            justify=LEFT,
            width=10)
        self.end_label = ttk.Label(
            frame,
            text='End time of video in format 00:00:00',
            font=(
                'Helvetica',
                10),
            justify=LEFT)
        self.end_entry = ttk.Entry(
            frame,
            textvariable=self.end_time,
            font=(
                'Helvetica',
                10),
            width=10,
            justify=LEFT)
        self.image_label = ttk.Label(
            frame, textvariable=self.image_text, font=(
                'Helvetica', 10), justify=LEFT)
        self.image_button = Button(
            frame,
            text='Click to set',
            font=(
                'Helvetica',
                10),
            command=self._get_thumbnail,
            justify=LEFT)
        self.title_label = ttk.Label(
            frame, text="Title of the video", font=(
                'Helvetica', 10), justify=LEFT)
        self.title_entry = ttk.Entry(
            frame,
            textvariable=self.title,
            font=(
                'Helvetica',
                10),
            width=20,
            justify=LEFT)
        self.process_button = Button(
            frame,
            text='Trim/Upload',
            font=(
                'Helvetica',
                10,
                'bold'),
            command=self._trim_and_upload,
            justify=LEFT)

        self.image_text.set("Path to thumbnail image (optional)")

        self.start_label.grid(sticky=W, row=1, column=0, padx=5, pady=5)
        self.start_entry.grid(sticky=W, row=1, column=1, padx=5, pady=5)
        self.end_label.grid(sticky=W, row=2, column=0, padx=5, pady=5)
        self.end_entry.grid(sticky=W, row=2, column=1, padx=5, pady=5)
        self.image_label.grid(sticky=W, row=3, column=0, padx=5, pady=5)
        self.image_button.grid(sticky=W, row=3, column=1, padx=5, pady=5)
        self.title_label.grid(sticky=W, row=4, column=0, padx=5, pady=5)
        self.title_entry.grid(sticky=W, row=4, column=1, padx=5, pady=5)
        self.process_button.grid(sticky=W, row=5, column=1, padx=5, pady=5)

    def _get_thumbnail(self) -> None:
        new_thumbnail_path = filedialog.askopenfilename(
            title='Select image file', filetypes=[
                ('All Images', ('*.jpg', '*.png'))])
        if new_thumbnail_path not in (
                '', self.thumbnail_handler.thumbnail_path):
            self.image_text.set('Thumbnail path: ' + new_thumbnail_path)
            self.thumbnail_handler.thumbnail_path = new_thumbnail_path

    def _enable_overlay_forms(self) -> None:
        self.start_entry['state'] = 'enabled'
        self.end_entry['state'] = 'enabled'
        self.title_entry['state'] = 'enabled'
        self.image_button['state'] = 'active'

    def _disable_overlay_forms(self) -> None:
        self.start_entry['state'] = 'disabled'
        self.end_entry['state'] = 'disabled'
        self.title_entry['state'] = 'disabled'
        self.image_button['state'] = 'disabled'

    def _clear_overlay_forms(self) -> None:
        self.start_time.set("")
        self.end_time.set("")
        self.image_text.set("Path to thumbnail image (optional)")
        self.thumbnail_handler.thumbnail_path = ""
        self.title.set("")

    def _schedule_check(self, thread):
        root.after(1000, _check_if_done, thread)

    def _check_if_done(self, thread):
        if not thread.is_alive():
            _enable_all_forms()
        else:
            _schedule_check(thread)

    def _trim_and_upload(self) -> None:
        def trim_and_upload():
            try:
                vimeo_client_config = get_vimeo_client_configuration(
                    app_directory_config.get_vimeo_config_file_path())
                video_trim_upload_config = get_video_trim_upload_configuration(
                    self.video_id,
                    self.video_path,
                    self.resolution,
                    self.start_time.get().strip(),
                    self.end_time.get().strip(),
                    self.title.get(),
                    self.thumbnail_handler.thumbnail_path)
                driver.update_vimeo_client_config(vimeo_client_config)
                download_video_path = driver.trim_resource(
                    video_trim_upload_config)
                video_url = driver.upload_video(
                    download_video_path,
                    video_trim_upload_config.video_title,
                    video_trim_upload_config.image_url)
                # Open the url in browser, if possible
                webbrowser.open_new(video_url)
                messagebox.showinfo(
                    "Upload status",
                    f"Finished uploading video to Vimeo for YouTube video with ID [{video_trim_upload_config.video_id}]")
            except vimeo.exceptions.VideoUploadFailure:
                messagebox.showerror(
                    'Error', 'Failed to download the video with input configuration!')

        _disable_all_forms()
        thread = threading.Thread(target=trim_and_upload())
        thread.start()
        _schedule_check(thread)


def _initialize_directories() -> AppDirectoryConfiguration:
    """
    Initialize the environment folders and configuration files
    :return: None
    """
    ops = platform.system()
    if ops == 'Windows':
        documents_folder = 'My Documents'
    elif ops == 'Darwin':
        documents_folder = 'Documents'
    else:
        logging.info("Running on unsupported os %s", ops)
        sys.exit(1)
    root_dir = os.path.join(
        os.path.expanduser('~'),
        documents_folder,
        APP_DIRECTORY_NAME)
    if not os.path.exists(root_dir):
        logging.info("Creating dir under %s", root_dir)
        os.mkdir(root_dir)
    video_root_dir = os.path.join(root_dir, 'videos')
    if not os.path.exists(video_root_dir):
        logging.info("Creating video dir under %s", video_root_dir)
        os.mkdir(video_root_dir)
    configs_root_dir = os.path.join(root_dir, 'configs')
    if not os.path.exists(configs_root_dir):
        logging.info("Creating configs dir under %s", configs_root_dir)
        os.mkdir(configs_root_dir)
    return AppDirectoryConfiguration(
        root_dir, video_root_dir, configs_root_dir)


def _download_video() -> None:
    def download():
        try:
            video_download_config = VideoDownloadConfiguration(
                video_id_str.get(), resolution.get())
            download_video_path = driver.download(video_download_config)
            subprocess.Popen(["python", os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "../gui/video_player.py"), download_video_path])
            logging.info(
                "Finished uploading video to Vimeo for YouTube video with ID %s",
                video_download_config.video_id)
            PostDownloadProcessor(download_video_path)
        except vimeo.exceptions.VideoUploadFailure:
            messagebox.showerror(
                'Error', 'Failed to download the video with input configuration!')

    _disable_download_button()
    thread = threading.Thread(target=download)
    thread.start()
    _schedule_check(thread)


def _import_vimeo_client_config_yaml() -> None:
    filename = filedialog.askopenfilename(
        title='Select config file for Vimeo client', filetypes=[
            ('Vimeo config files', '*.bin')])
    try:
        driver.update_vimeo_client_config(
            get_vimeo_client_configuration(filename))
        # Copy the file over to target config path
        shutil.copy(
            filename,
            app_directory_config.get_vimeo_config_file_path())
    except UnsetConfigurationException:
        logging.warning("Configuration path is not set")
    except PermissionError:
        logging.error("Permission error to read or copy the file")
    except VimeoClientConfigurationException:
        logging.error("Config file is not valid format")


def _enable_download_button() -> None:
    video_id_entry['state'] = 'active'
    resolution_option['state'] = 'active'
    download_button['state'] = 'normal'
    download_button['text'] = 'Start Downloading'


def _disable_download_button() -> None:
    video_id_entry['state'] = 'disabled'
    resolution_option['state'] = 'disabled'
    download_button['state'] = 'disabled'
    download_button['text'] = 'In Progress...'


def _schedule_check(thread):
    root.after(1000, _check_if_done, thread)


def _check_if_done(thread):
    if not thread.is_alive():
        _enable_download_button()
    else:
        _schedule_check(thread)


def _check_if_requirements_met() -> None:
    """
    Check if requirements to run the uploader is satisfied
    :return:
    """
    ffmpeg_exists = shutil.which("ffmpeg") is not None
    if not ffmpeg_exists:
        logging.info("User does not have FFmpeg installed")
        messagebox.showerror(
            'Error',
            'System requirements are not met. FFmpeg is required to be downloaded for the application to run.\n'
            'Please download from https://ffmpeg.org/')
        sys.exit(1)


def _enable_video_id() -> None:
    video_id_entry['state'] = 'active'
    resolution_option['state'] = 'disabled'
    download_button['state'] = 'disabled'


def _enable_all_forms() -> None:
    resolution_option['state'] = 'active'
    download_button['state'] = 'active'


def _disable_all_forms() -> None:
    video_id_entry['state'] = 'disabled'
    resolution_option['state'] = 'disabled'
    download_button['state'] = 'disabled'


def _get_video_metadata(video_id: str) -> None:
    def _update_video_resolution_dropdown() -> None:
        resolution_option["menu"].delete(0, "end")
        for item in video_resolutions:
            resolution_option["menu"].add_command(
                label=item,
                command=lambda value=item: resolution.set(value)
            )
        resolution.set(video_resolutions[0])

    def format_time(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours} hour(s) {minutes} minute(s) {seconds} second(s)"

    def _process_video_information() -> bool:
        if video_metadata is None:
            return False
        else:
            date_format = "%Y-%m-%d"
            info_dump = f"Title: {video_metadata.title}...\nAuthor: {video_metadata.author}\n" \
                        f"Length: {format_time(video_metadata.length_in_sec)}\n" \
                        f"Publish Date: {video_metadata.publish_date.strftime(date_format)}"
            return messagebox.askyesno(
                'Video select pop-up',
                f'Use video with information below?\n\n{info_dump}')

    def _get_resolution_sort_key(res: str) -> int:
        return int(res[:-1])

    proceed = False
    try:
        video_metadata = driver.get_video_metadata(
            input_service, video_id)
        proceed = _process_video_information()
    except VideoUnavailable as error:
        logging.warning(error)
    except RegexMatchError as error:
        logging.debug(error)
    finally:
        if proceed:
            video_resolutions = sorted(
                [res for res in video_metadata.resolutions if res], key=_get_resolution_sort_key, reverse=True)
            _enable_all_forms()
        else:
            video_resolutions = ['N/A']
            _enable_video_id()
        _update_video_resolution_dropdown()


_check_if_requirements_met()

driver = Driver()
app_directory_config = _initialize_directories()
driver.update_app_directory_config(app_directory_config)
driver.update_vimeo_client_config(
    get_vimeo_client_configuration(
        app_directory_config.get_vimeo_config_file_path()))

input_service: SupportedServices = SupportedServices.YOUTUBE
output_service: SupportedServices = SupportedServices.VIMEO

driver.update_download_service(input_service)
driver.update_upload_service(output_service)

# Root element
root = Tk()
root.title("Vimeo Uploader")

# String Var
video_id_str = StringVar()
video_information_str = StringVar()
resolution = StringVar()

# Boolean Var
input_youtube_source = BooleanVar()
input_youtube_source.set(True)
output_vimeo_source = BooleanVar()
output_vimeo_source.set(True)

video_id_label = ttk.Label(
    root, text='Video ID', font=(
        'Helvetica', 10), justify=LEFT)
video_id_entry = ttk.Entry(
    root, textvariable=video_id_str, font=(
        'Helvetica', 10), width=15, justify=LEFT)
video_information_label = ttk.Label(
    root, text='', font=(
        'Helvetica', 10), justify=LEFT)
resolution_label = ttk.Label(
    root, text='Video resolution (e.g. 1080p)', font=(
        'Helvetica', 10), justify=LEFT)
resolution_option = ttk.OptionMenu(
    root,
    resolution,
    EMPTY_RESOLUTION[0],
    *EMPTY_RESOLUTION)
download_button = Button(
    root,
    text='Start Downloading',
    font=(
        'Helvetica',
        10,
        'bold'),
    command=_download_video,
    justify=LEFT)

menubar = Menu(
    root,
    background='#ff8000',
    foreground='black',
    activebackground='white',
    activeforeground='black')
file = Menu(menubar, tearoff=0)
file.add_command(label='About', command=_about)
file.add_command(label='Quit', command=root.quit)

input_video_source = Menu(menubar, tearoff=0)
input_video_source.add_checkbutton(
    label='YouTube',
    onvalue=1,
    offvalue=0,
    variable=input_youtube_source)
# input_video_source.add_checkbutton(label='Vimeo')

output_video_source = Menu(menubar, tearoff=0)
# output_video_source.add_checkbutton(label='YouTube')
output_video_source.add_checkbutton(
    label='Vimeo',
    onvalue=1,
    offvalue=0,
    variable=output_vimeo_source)

source = Menu(menubar, tearoff=0)
source.add_cascade(
    label='Input Video Service',
    menu=input_video_source)
source.add_cascade(
    label='Output Video Service',
    menu=output_video_source)
source.add_separator()
source.add_command(
    label='Import Vimeo Config',
    command=_import_vimeo_client_config_yaml)

menubar.add_cascade(label='File', menu=file)
menubar.add_cascade(label='Service Configuration', menu=source)

root.config(menu=menubar)
video_id_str.trace(
    "w",
    lambda name,
    index,
    mode,
    video_id=video_id_str: _get_video_metadata(
        video_id.get()))

video_id_label.grid(sticky=W, row=1, column=0, padx=5, pady=5)
video_id_entry.grid(sticky=W, row=1, column=1, padx=5, pady=5)
video_information_label.grid(sticky=W, row=1, column=2, padx=5, pady=5)
resolution_label.grid(sticky=W, row=2, column=0, padx=5, pady=5)
resolution_option.grid(sticky=W, row=2, column=1, padx=5, pady=5)
download_button.grid(sticky=W, row=3, column=1, padx=5, pady=5)

# most forms disabled by default
_enable_video_id()
root.mainloop()
