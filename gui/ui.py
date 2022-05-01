import logging
import os.path
import platform
import shutil
import sys
import threading
from tkinter import Tk, Menu, StringVar, messagebox, LEFT, W, filedialog, Button, ttk

import vimeo
from pytube import YouTube
from pytube.exceptions import RegexMatchError

from core.driver import Driver
from core.exceptions import VimeoConfigurationException
from core.util import get_vimeo_configuration, get_video_configuration, get_youtube_url
from model.config import AppDirectoryConfiguration, YoutubeVideoMetadata

root = Tk()
root.title("Vimeo Uploader")
root.geometry('640x480')

thumbnail_path: str = None
empty_resolution = ['N/A']
app_directory_name = "Vimeo Uploader"
app_directory_config: AppDirectoryConfiguration = None


def _about() -> None:
    messagebox.showinfo('About', 'This is a python-based application to download youtube videos, trim them, '
                                 'and re-upload to Vimeo.')


def _import_config_yaml() -> None:
    filename = filedialog.askopenfilename(title='Select config file', filetypes=[('Config files', '*.yaml')])
    try:
        get_vimeo_configuration(filename)
        shutil.copy(filename, app_directory_config.get_vimeo_config_file_path())
    except VimeoConfigurationException:
        logging.error("Config file is not valid format")


def _get_thumbnail() -> None:
    global thumbnail_path
    new_thumbnail_path = filedialog.askopenfilename(title='Select image file',
                                                    filetypes=[('All Images', ('*.jpg', '*.png'))])
    if new_thumbnail_path != '' and new_thumbnail_path != thumbnail_path:
        thumbnail_path = new_thumbnail_path
        image_text.set('Thumbnail path: ' + new_thumbnail_path)


def _get_video_metadata(video_id: str) -> None:
    video_id = video_id.get()
    video_resolutions = []
    video_metadata = None

    def _update_video_resolution_dropdown() -> None:
        resolution_option["menu"].delete(0, "end")
        for item in video_resolutions:
            resolution_option["menu"].add_command(
                label=item,
                command=lambda value=item: resolution.set(value)
            )
        resolution.set(video_resolutions[-1])

    def _update_video_information() -> None:
        if video_metadata is not None:
            info_dump = f"Title: {video.title[0:20]}...\nAuthor: {video.author}\nLength: {video.length} " \
                        f"seconds\nPublish Date: {video.publish_date}"
            messagebox.showinfo('Video Information', info_dump)

    def _get_resolution_sort_key(res: str) -> int:
        return int(res[:-1])

    new_video_resolutions = set()
    new_video_metadata = None
    try:
        video = YouTube(get_youtube_url(video_id))
        new_video_metadata = YoutubeVideoMetadata(video.video_id, video.title, video.author, video.length,
                                                  video.publish_date)
        logging.info(f"Video metadata: {video.video_id}, {video.title}, {video.author}, {video.length}, "
                     f"{video.publish_date}")
        for stream in video.streams:
            new_video_resolutions.add(stream.resolution)
    except RegexMatchError as e:
        logging.debug(e)
    if new_video_metadata is None:
        video_resolutions = ['N/A']
        video_metadata = None
    else:
        # Update video resolutions
        video_resolutions = sorted([res for res in new_video_resolutions if res], key=_get_resolution_sort_key)
        video_metadata = new_video_metadata
    _update_video_information()
    _update_video_resolution_dropdown()


def enable_process_button() -> None:
    process_button['state'] = 'normal'
    process_button['text'] = 'Start Processing'


def disable_process_button() -> None:
    process_button['state'] = 'disabled'
    process_button['text'] = 'In Progress...'


def process_video() -> None:
    def process():
        try:
            vimeo_config = get_vimeo_configuration(app_directory_config.get_vimeo_config_file_path())
            driver = Driver(vimeo_config, app_directory_config)
            video_config = get_video_configuration(video_id_str.get(), start_time.get().strip(),
                                                   end_time.get().strip(),
                                                   resolution.get(), title.get(), thumbnail_path)
            driver.process(video_config)
        except vimeo.exceptions.VideoUploadFailure:
            messagebox.showerror('Error', 'Failed to process the video with input configuration!')

    disable_process_button()
    th = threading.Thread(target=process)
    th.start()
    _schedule_check(th)


def _schedule_check(thread):
    root.after(1000, _check_if_done, thread)


def _check_if_done(thread):
    if not thread.is_alive():
        enable_process_button()
    else:
        _schedule_check(thread)


def init() -> None:
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
        logging.info("Running on unsupported os " + ops)
        sys.exit(1)
    root_dir = os.path.join(os.path.expanduser('~'), documents_folder, app_directory_name)
    if not os.path.exists(root_dir):
        logging.info("Creating dir under " + root_dir)
        os.mkdir(root_dir)
    video_root_dir = os.path.join(root_dir, 'videos')
    if not os.path.exists(video_root_dir):
        logging.info("Creating video dir under " + video_root_dir)
        os.mkdir(video_root_dir)
    configs_root_dir = os.path.join(root_dir, 'configs')
    if not os.path.exists(configs_root_dir):
        logging.info("Creating configs dir under " + configs_root_dir)
        os.mkdir(configs_root_dir)
    global app_directory_config
    app_directory_config = AppDirectoryConfiguration(root_dir, video_root_dir, configs_root_dir)


init()

menubar = Menu(root, background='#ff8000', foreground='black', activebackground='white', activeforeground='black')
file = Menu(menubar, tearoff=1)
file.add_command(label='About', command=_about)
file.add_command(label='Import config', command=_import_config_yaml)
file.add_command(label='Quit', command=root.quit)
menubar.add_cascade(label='File', menu=file)

root.config(menu=menubar)

video_id_str = StringVar()
video_id_str.trace("w", lambda name, index, mode, video_id=video_id_str: _get_video_metadata(video_id))
video_information_str = StringVar()
start_time = StringVar()
end_time = StringVar()
image_text = StringVar()
image_text.set("Path to thumbnail image (optional)")
resolution = StringVar()
title = StringVar()

video_id_label = ttk.Label(root, text='Video ID', font=('Helvetica', 10), justify=LEFT)
video_id_entry = ttk.Entry(root, textvariable=video_id_str, font=('Helvetica', 10), width=15, justify=LEFT)
video_information_label = ttk.Label(root, text='', font=('Helvetica', 10), justify=LEFT)
start_label = ttk.Label(root, text='Start time of video in format 00:00:00', font=('Helvetica', 10), justify=LEFT)
start_entry = ttk.Entry(root, textvariable=start_time, font=('Helvetica', 10), justify=LEFT, width=10)
end_label = ttk.Label(root, text='End time of video in format 00:00:00', font=('Helvetica', 10), justify=LEFT)
end_entry = ttk.Entry(root, textvariable=end_time, font=('Helvetica', 10), width=10, justify=LEFT)
image_label = ttk.Label(root, textvariable=image_text, font=('Helvetica', 10), justify=LEFT)
image_button = Button(root, text='Click to set', font=('Helvetica', 10), command=_get_thumbnail, justify=LEFT)
resolution_label = ttk.Label(root, text='Video resolution (e.g. 1080p)', font=('Helvetica', 10), justify=LEFT)
resolution_option = ttk.OptionMenu(root, resolution, empty_resolution[0], *empty_resolution)
title_label = ttk.Label(root, text="Title of the video", font=('Helvetica', 10), justify=LEFT)
title_entry = ttk.Entry(root, textvariable=title, font=('Helvetica', 10), width=20, justify=LEFT)

process_button = Button(root, text='Start Processing', font=('Helvetica', 10, 'bold'), command=process_video,
                        justify=LEFT)

video_id_label.grid(sticky=W, row=1, column=0)
video_id_entry.grid(sticky=W, row=1, column=1)
video_information_label.grid(sticky=W, row=1, column=2)
start_label.grid(sticky=W, row=2, column=0)
start_entry.grid(sticky=W, row=2, column=1)
end_label.grid(sticky=W, row=3, column=0)
end_entry.grid(sticky=W, row=3, column=1)
image_label.grid(sticky=W, row=4, column=0)
image_button.grid(sticky=W, row=4, column=1)
resolution_label.grid(sticky=W, row=5, column=0)
resolution_option.grid(sticky=W, row=5, column=1)
title_label.grid(sticky=W, row=6, column=0)
title_entry.grid(sticky=W, row=6, column=1)
process_button.grid(sticky=W, row=7, column=1)

root.mainloop()
