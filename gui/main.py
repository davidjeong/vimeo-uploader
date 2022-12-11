"""
Main entry for GUI
"""

import logging
import shutil
import sys
import threading
from dataclasses import dataclass
from tkinter import Tk, Menu, StringVar, messagebox, LEFT, W, filedialog, Button, ttk, BooleanVar

import vimeo
from pytube.exceptions import RegexMatchError, VideoUnavailable

from core.driver import Driver, initialize_directories
from core.streaming_service import SupportedServices
from core.util import get_vimeo_client_configuration, get_video_configuration
from model.exception import VimeoClientConfigurationException, UnsetConfigurationException

EMPTY_RESOLUTION = ['N/A']


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


def _process_video() -> None:
    def process():
        try:
            vimeo_client_config = get_vimeo_client_configuration(
                app_directory_config.get_vimeo_config_file_path())
            video_config = get_video_configuration(
                video_id_str.get(),
                start_time.get().strip(),
                end_time.get().strip(),
                resolution.get(),
                title.get(),
                thumbnail_handler.thumbnail_path)
            driver.update_vimeo_client_config(vimeo_client_config)
            driver.process(video_config)
            messagebox.showinfo(
                "Upload status",
                f"Finished uploading video to Vimeo for YouTube video with ID [{video_config.video_id}]")
        except vimeo.exceptions.VideoUploadFailure:
            messagebox.showerror(
                'Error', 'Failed to process the video with input configuration!')

    _disable_process_button()
    thread = threading.Thread(target=process)
    thread.start()
    _schedule_check(thread)


def _get_thumbnail() -> None:
    new_thumbnail_path = filedialog.askopenfilename(
        title='Select image file', filetypes=[
            ('All Images', ('*.jpg', '*.png'))])
    if new_thumbnail_path not in (
            '', thumbnail_handler.thumbnail_path):
        image_text.set('Thumbnail path: ' + new_thumbnail_path)
        thumbnail_handler.thumbnail_path = new_thumbnail_path


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


def _enable_process_button() -> None:
    process_button['state'] = 'normal'
    process_button['text'] = 'Start Processing'


def _disable_process_button() -> None:
    process_button['state'] = 'disabled'
    process_button['text'] = 'In Progress...'


def _schedule_check(thread):
    root.after(1000, _check_if_done, thread)


def _check_if_done(thread):
    if not thread.is_alive():
        _enable_process_button()
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


def _enable_all_forms() -> None:
    start_entry['state'] = 'enabled'
    end_entry['state'] = 'enabled'
    image_button['state'] = 'active'
    title_entry['state'] = 'enabled'
    process_button['state'] = 'active'


def _disable_all_forms() -> None:
    start_entry['state'] = 'disabled'
    end_entry['state'] = 'disabled'
    image_button['state'] = 'disabled'
    title_entry['state'] = 'disabled'
    process_button['state'] = 'disabled'


def _clear_all_forms() -> None:
    start_time.set("")
    end_time.set("")
    image_text.set("Path to thumbnail image (optional)")
    thumbnail_handler.thumbnail_path = ""
    title.set("")


def _get_video_metadata(video_id: str) -> None:
    def _update_video_resolution_dropdown() -> None:
        resolution_option["menu"].delete(0, "end")
        for item in video_resolutions:
            resolution_option["menu"].add_command(
                label=item,
                command=lambda value=item: resolution.set(value)
            )
        resolution.set(video_resolutions[-1])

    def format_time(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours} hour(s) {minutes} minute(s) {seconds} second(s)"

    def _process_video_information() -> bool:
        if video_metadata is None:
            return False
        else:
            info_dump = f"Title: {video_metadata.title}...\nAuthor: {video_metadata.author}\n" \
                        f"Length: {format_time(video_metadata.length_in_sec)}\n" \
                        f"Length: {video_metadata.length_in_sec} " \
                        f"Publish Date: {video_metadata.publish_date}"
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
                [res for res in video_metadata.resolutions if res], key=_get_resolution_sort_key)
            _enable_all_forms()
        else:
            video_resolutions = ['N/A']
            _clear_all_forms()
            _disable_all_forms()
        _update_video_resolution_dropdown()


_check_if_requirements_met()

driver = Driver()
thumbnail_handler = ThumbnailHandler()
app_directory_config = initialize_directories()
driver.update_app_directory_config(app_directory_config)
try:
    driver.update_vimeo_client_config(
        get_vimeo_client_configuration(
            app_directory_config.get_vimeo_config_file_path()))
except UnsetConfigurationException:
    logging.error("Failed to get the config file from path")

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
start_time = StringVar()
end_time = StringVar()
image_text = StringVar()
resolution = StringVar()
title = StringVar()

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
start_label = ttk.Label(
    root,
    text='Start time of video in format 00:00:00',
    font=(
        'Helvetica',
        10),
    justify=LEFT)
start_entry = ttk.Entry(
    root,
    textvariable=start_time,
    font=(
        'Helvetica',
        10),
    justify=LEFT,
    width=10)
end_label = ttk.Label(
    root,
    text='End time of video in format 00:00:00',
    font=(
        'Helvetica',
        10),
    justify=LEFT)
end_entry = ttk.Entry(
    root,
    textvariable=end_time,
    font=(
        'Helvetica',
        10),
    width=10,
    justify=LEFT)
image_label = ttk.Label(
    root, textvariable=image_text, font=(
        'Helvetica', 10), justify=LEFT)
image_button = Button(
    root,
    text='Click to set',
    font=(
        'Helvetica',
        10),
    command=_get_thumbnail,
    justify=LEFT)
resolution_label = ttk.Label(
    root, text='Video resolution (e.g. 1080p)', font=(
        'Helvetica', 10), justify=LEFT)
resolution_option = ttk.OptionMenu(
    root,
    resolution,
    EMPTY_RESOLUTION[0],
    *EMPTY_RESOLUTION)
title_label = ttk.Label(
    root, text="Title of the video", font=(
        'Helvetica', 10), justify=LEFT)
title_entry = ttk.Entry(
    root,
    textvariable=title,
    font=(
        'Helvetica',
        10),
    width=20,
    justify=LEFT)
process_button = Button(
    root,
    text='Start Processing',
    font=(
        'Helvetica',
        10,
        'bold'),
    command=_process_video,
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

image_text.set("Path to thumbnail image (optional)")

video_id_label.grid(sticky=W, row=1, column=0, padx=5, pady=5)
video_id_entry.grid(sticky=W, row=1, column=1, padx=5, pady=5)
video_information_label.grid(sticky=W, row=1, column=2, padx=5, pady=5)
start_label.grid(sticky=W, row=2, column=0, padx=5, pady=5)
start_entry.grid(sticky=W, row=2, column=1, padx=5, pady=5)
end_label.grid(sticky=W, row=3, column=0, padx=5, pady=5)
end_entry.grid(sticky=W, row=3, column=1, padx=5, pady=5)
image_label.grid(sticky=W, row=4, column=0, padx=5, pady=5)
image_button.grid(sticky=W, row=4, column=1, padx=5, pady=5)
resolution_label.grid(sticky=W, row=5, column=0, padx=5, pady=5)
resolution_option.grid(sticky=W, row=5, column=1, padx=5, pady=5)
title_label.grid(sticky=W, row=6, column=0, padx=5, pady=5)
title_entry.grid(sticky=W, row=6, column=1, padx=5, pady=5)
process_button.grid(sticky=W, row=7, column=1, padx=5, pady=5)

# most forms disabled by default
_disable_all_forms()
root.mainloop()
