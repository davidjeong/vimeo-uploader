"""
Main entry for GUI
"""

import logging
import os.path
import platform
import shutil
import sys
import threading
from dataclasses import dataclass
from tkinter import Tk, Menu, StringVar, messagebox, LEFT, W, filedialog, Button, ttk

import vimeo
from pytube.exceptions import RegexMatchError, VideoUnavailable

from core.driver import Driver
from core.streaming_service import SupportedServices
from core.util import get_vimeo_client_configuration, get_video_configuration
from model.config import AppDirectoryConfiguration
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


class VimeoUploader:
    """
    Main class for vimeo uploader
    """

    def __init__(self):

        self.driver = Driver()
        self.thumbnail_handler = ThumbnailHandler()
        self.app_directory_config = self._initialize_directories()
        self.driver.update_app_directory_config(self.app_directory_config)
        self.driver.update_vimeo_client_config(
            get_vimeo_client_configuration(
                self.app_directory_config.get_vimeo_config_file_path()))

        self.input_service: SupportedServices = SupportedServices.YOUTUBE
        self.output_service: SupportedServices = SupportedServices.VIMEO

        self.driver.update_download_service(self.input_service)
        self.driver.update_upload_service(self.output_service)

        # Root element
        self.root = Tk()
        # String Var
        self.video_id_str = StringVar()
        self.video_information_str = StringVar()
        self.start_time = StringVar()
        self.end_time = StringVar()
        self.image_text = StringVar()
        self.resolution = StringVar()
        self.title = StringVar()

        self.video_id_label = ttk.Label(
            self.root, text='Video ID', font=(
                'Helvetica', 10), justify=LEFT)
        self.video_id_entry = ttk.Entry(
            self.root, textvariable=self.video_id_str, font=(
                'Helvetica', 10), width=15, justify=LEFT)
        self.video_information_label = ttk.Label(
            self.root, text='', font=(
                'Helvetica', 10), justify=LEFT)
        self.start_label = ttk.Label(
            self.root,
            text='Start time of video in format 00:00:00',
            font=(
                'Helvetica',
                10),
            justify=LEFT)
        self.start_entry = ttk.Entry(
            self.root,
            textvariable=self.start_time,
            font=(
                'Helvetica',
                10),
            justify=LEFT,
            width=10)
        self.end_label = ttk.Label(
            self.root,
            text='End time of video in format 00:00:00',
            font=(
                'Helvetica',
                10),
            justify=LEFT)
        self.end_entry = ttk.Entry(
            self.root,
            textvariable=self.end_time,
            font=(
                'Helvetica',
                10),
            width=10,
            justify=LEFT)
        self.image_label = ttk.Label(
            self.root, textvariable=self.image_text, font=(
                'Helvetica', 10), justify=LEFT)
        self.image_button = Button(
            self.root,
            text='Click to set',
            font=(
                'Helvetica',
                10),
            command=self._get_thumbnail,
            justify=LEFT)
        self.resolution_label = ttk.Label(
            self.root, text='Video resolution (e.g. 1080p)', font=(
                'Helvetica', 10), justify=LEFT)
        self.resolution_option = ttk.OptionMenu(
            self.root,
            self.resolution,
            EMPTY_RESOLUTION[0],
            *EMPTY_RESOLUTION)
        self.title_label = ttk.Label(
            self.root, text="Title of the video", font=(
                'Helvetica', 10), justify=LEFT)
        self.title_entry = ttk.Entry(
            self.root,
            textvariable=self.title,
            font=(
                'Helvetica',
                10),
            width=20,
            justify=LEFT)
        self.process_button = Button(
            self.root,
            text='Start Processing',
            font=(
                'Helvetica',
                10,
                'bold'),
            command=self._process_video,
            justify=LEFT)

    def _get_thumbnail(self) -> None:
        new_thumbnail_path = filedialog.askopenfilename(
            title='Select image file', filetypes=[
                ('All Images', ('*.jpg', '*.png'))])
        if new_thumbnail_path not in (
                '', self.thumbnail_handler.thumbnail_path):
            self.image_text.set('Thumbnail path: ' + new_thumbnail_path)
            self.thumbnail_handler.thumbnail_path = new_thumbnail_path

    @staticmethod
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

    def _import_vimeo_client_config_yaml(self) -> None:
        filename = filedialog.askopenfilename(
            title='Select config file for Vimeo client', filetypes=[
                ('Vimeo config files', '*.bin')])
        try:
            self.driver.update_vimeo_client_config(
                get_vimeo_client_configuration(filename))
            # Copy the file over to target config path
            shutil.copy(
                filename,
                self.app_directory_config.get_vimeo_config_file_path())
        except UnsetConfigurationException:
            logging.warning("Configuration path is not set")
        except PermissionError:
            logging.error("Permission error to read or copy the file")
        except VimeoClientConfigurationException:
            logging.error("Config file is not valid format")

    def _enable_process_button(self) -> None:
        self.process_button['state'] = 'normal'
        self.process_button['text'] = 'Start Processing'

    def _disable_process_button(self) -> None:
        self.process_button['state'] = 'disabled'
        self.process_button['text'] = 'In Progress...'

    def _schedule_check(self, thread):
        self.root.after(1000, self._check_if_done, thread)

    def _check_if_done(self, thread):
        if not thread.is_alive():
            self._enable_process_button()
        else:
            self._schedule_check(thread)

    def drive(self):
        """
        Main driver of application
        :return:
        """
        self.root.title("Vimeo Uploader")
        self.root.geometry('640x480')

        menubar = Menu(
            self.root,
            background='#ff8000',
            foreground='black',
            activebackground='white',
            activeforeground='black')
        file = Menu(menubar, tearoff=0)
        file.add_command(label='About', command=_about)
        file.add_command(label='Quit', command=self.root.quit)

        input_video_source = Menu(menubar, tearoff=0)
        input_video_source.add_checkbutton(label='YouTube')
        input_video_source.add_checkbutton(label='Vimeo')

        output_video_source = Menu(menubar, tearoff=0)
        output_video_source.add_checkbutton(label='YouTube')
        output_video_source.add_checkbutton(label='Vimeo')

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
            command=self._import_vimeo_client_config_yaml)

        menubar.add_cascade(label='File', menu=file)
        menubar.add_cascade(label='Service Configuration', menu=source)

        self.root.config(menu=menubar)
        self.video_id_str.trace(
            "w",
            lambda name,
            index,
            mode,
            video_id=self.video_id_str: self._get_video_metadata(
                video_id.get()))

        self.image_text.set("Path to thumbnail image (optional)")

        self.video_id_label.grid(sticky=W, row=1, column=0)
        self.video_id_entry.grid(sticky=W, row=1, column=1)
        self.video_information_label.grid(sticky=W, row=1, column=2)
        self.start_label.grid(sticky=W, row=2, column=0)
        self.start_entry.grid(sticky=W, row=2, column=1)
        self.end_label.grid(sticky=W, row=3, column=0)
        self.end_entry.grid(sticky=W, row=3, column=1)
        self.image_label.grid(sticky=W, row=4, column=0)
        self.image_button.grid(sticky=W, row=4, column=1)
        self.resolution_label.grid(sticky=W, row=5, column=0)
        self.resolution_option.grid(sticky=W, row=5, column=1)
        self.title_label.grid(sticky=W, row=6, column=0)
        self.title_entry.grid(sticky=W, row=6, column=1)
        self.process_button.grid(sticky=W, row=7, column=1)

        # most forms disabled by default
        self._disable_all_forms()

        self.root.mainloop()

    def _process_video(self) -> None:
        def process():
            try:
                vimeo_client_config = get_vimeo_client_configuration(
                    self.app_directory_config.get_vimeo_config_file_path())
                video_config = get_video_configuration(
                    self.video_id_str.get(),
                    self.start_time.get().strip(),
                    self.end_time.get().strip(),
                    self.resolution.get(),
                    self.title.get(),
                    self.thumbnail_handler.thumbnail_path)
                self.driver.update_vimeo_client_config(vimeo_client_config)
                self.driver.process(video_config)
                messagebox.showinfo(
                    "Upload status",
                    f"Finished uploading video to Vimeo for YouTube video with ID [{video_config.video_id}]")
            except vimeo.exceptions.VideoUploadFailure:
                messagebox.showerror(
                    'Error', 'Failed to process the video with input configuration!')

        self._disable_process_button()
        thread = threading.Thread(target=process)
        thread.start()
        self._schedule_check(thread)

    def _enable_all_forms(self) -> None:
        self.start_entry['state'] = 'enabled'
        self.end_entry['state'] = 'enabled'
        self.image_button['state'] = 'active'
        self.title_entry['state'] = 'enabled'
        self.process_button['state'] = 'active'

    def _disable_all_forms(self) -> None:
        self.start_entry['state'] = 'disabled'
        self.end_entry['state'] = 'disabled'
        self.image_button['state'] = 'disabled'
        self.title_entry['state'] = 'disabled'
        self.process_button['state'] = 'disabled'

    def _clear_all_forms(self) -> None:
        self.start_time.set("")
        self.end_time.set("")
        self.image_text.set("Path to thumbnail image (optional)")
        self.thumbnail_handler.thumbnail_path = ""
        self.title.set("")

    def _get_video_metadata(self, video_id: str) -> None:

        def _update_video_resolution_dropdown() -> None:
            self.resolution_option["menu"].delete(0, "end")
            for item in video_resolutions:
                self.resolution_option["menu"].add_command(
                    label=item,
                    command=lambda value=item: self.resolution.set(value)
                )
            self.resolution.set(video_resolutions[-1])

        def _process_video_information() -> bool:
            if video_metadata is None:
                return False
            else:
                info_dump = f"Title: {video_metadata.title}...\nAuthor: {video_metadata.author}\n" \
                            f"Length: {video_metadata.length_in_sec} " \
                            f"seconds\nPublish Date: {video_metadata.publish_date}"
                return messagebox.askyesno(
                    'Video select pop-up',
                    f'Use video with information below?\n\n{info_dump}')

        def _get_resolution_sort_key(res: str) -> int:
            return int(res[:-1])

        proceed = False
        try:
            video_metadata = self.driver.get_video_metadata(
                self.input_service, video_id)
            proceed = _process_video_information()
        except VideoUnavailable as error:
            logging.warning(error)
        except RegexMatchError as error:
            logging.debug(error)
        finally:
            if proceed:
                video_resolutions = sorted(
                    [res for res in video_metadata.resolutions if res], key=_get_resolution_sort_key)
                self._enable_all_forms()
            else:
                video_resolutions = ['N/A']
                self._clear_all_forms()
                self._disable_all_forms()
            _update_video_resolution_dropdown()


if __name__ == "__main__":
    vimeo_uploader = VimeoUploader()
    vimeo_uploader.drive()
