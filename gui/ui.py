import logging
from threading import Thread
from tkinter import Tk, Menu, StringVar, messagebox, LEFT, W, filedialog, Button, ttk

from pytube import YouTube
from pytube.exceptions import RegexMatchError

from core.driver import Driver
from core.util import get_vimeo_configuration, get_video_configuration

root = Tk()

root.title("Vimeo Uploader")
root.geometry('640x480')

vimeo_config: str = None
thumbnail_path: str = None
url_prefix = 'https://www.youtube.com/watch?v='
empty_resolution = ['N/A']


def about() -> None:
    messagebox.showinfo('About', 'This is a python-based application to download youtube videos, trim them, '
                                 'and re-upload to Vimeo.')


def import_config_json() -> None:
    global vimeo_config
    filename = filedialog.askopenfilename(title='Select config file', filetypes=[('Config files', '*.json')])
    vimeo_config = filename


def get_thumbnail() -> None:
    global thumbnail_path
    new_thumbnail_path = filedialog.askopenfilename(title='Select image file',
                                                    filetypes=[('All Images', ('*.jpg', '*.png'))])
    if new_thumbnail_path != '' and new_thumbnail_path != thumbnail_path:
        thumbnail_path = new_thumbnail_path
        image_text.set('Thumbnail path: ' + new_thumbnail_path)


def callback_video_resolution(url) -> None:
    new_url = url.get()
    video_resolutions = []

    def update_video_resolution_dropdown() -> None:
        resolution_option["menu"].delete(0, "end")
        for item in video_resolutions:
            resolution_option["menu"].add_command(
                label=item,
                command=lambda value=item: resolution.set(value)
            )
        resolution.set(video_resolutions[-1])

    def get_sort_key(res: str) -> int:
        return int(res[:-1])

    new_video_resolutions = set()
    try:
        video = YouTube(url_prefix + new_url)
        for stream in video.streams:
            new_video_resolutions.add(stream.resolution)
    except RegexMatchError as e:
        logging.warning(e)
    if len(new_video_resolutions) == 0:
        video_resolutions = ['N/A']
    else:
        video_resolutions = sorted([res for res in new_video_resolutions if res], key=get_sort_key)
    update_video_resolution_dropdown()


def enable_process_button() -> None:
    process_button['state'] = 'normal'
    process_button['text'] = 'Start Processing'


def disable_process_button() -> None:
    process_button['state'] = 'disabled'
    process_button['text'] = 'In Progress...'


def process_video() -> None:
    def process():
        disable_process_button()
        try:
            config = get_vimeo_configuration(vimeo_config)
            driver = Driver(config)
            video_config = get_video_configuration(url_prefix + url.get(), start_time.get().strip(),
                                                   end_time.get().strip(),
                                                   resolution.get(), title.get(), thumbnail_path)
            driver.process(video_config)
        except Exception as e:
            messagebox.showerror('Error', 'Failed to process the video with input configuration!')
        enable_process_button()

    th = Thread(target=process())
    th.start()


menubar = Menu(root, background='#ff8000', foreground='black', activebackground='white', activeforeground='black')
file = Menu(menubar, tearoff=1)
file.add_command(label='About', command=about)
file.add_command(label='Import config', command=import_config_json)
file.add_command(label='Quit', command=root.quit)
menubar.add_cascade(label='File', menu=file)

root.config(menu=menubar)

url = StringVar()
url.trace("w", lambda name, index, mode, url=url: callback_video_resolution(url))
start_time = StringVar()
end_time = StringVar()
image_text = StringVar()
image_text.set("Path to thumbnail image (optional)")
resolution = StringVar()
title = StringVar()

url_label = ttk.Label(root, text='Supplied link: ' + url_prefix, font=('Helvetica', 10), justify=LEFT)
url_entry = ttk.Entry(root, textvariable=url, font=('Helvetica', 10), width=15, justify=LEFT)
start_label = ttk.Label(root, text='Start time of video in format 00:00:00', font=('Helvetica', 10), justify=LEFT)
start_entry = ttk.Entry(root, textvariable=start_time, font=('Helvetica', 10), justify=LEFT, width=10)
end_label = ttk.Label(root, text='End time of video in format 00:00:00', font=('Helvetica', 10), justify=LEFT)
end_entry = ttk.Entry(root, textvariable=end_time, font=('Helvetica', 10), width=10, justify=LEFT)
image_label = ttk.Label(root, textvariable=image_text, font=('Helvetica', 10), justify=LEFT)
image_button = Button(root, text='Click to set', font=('Helvetica', 10), command=get_thumbnail, justify=LEFT)
resolution_label = ttk.Label(root, text='Video resolution (e.g. 1080p)', font=('Helvetica', 10), justify=LEFT)
resolution_option = ttk.OptionMenu(root, resolution, empty_resolution[0], *empty_resolution)
title_label = ttk.Label(root, text="Title of the video", font=('Helvetica', 10), justify=LEFT)
title_entry = ttk.Entry(root, textvariable=title, font=('Helvetica', 10), width=20, justify=LEFT)

process_button = Button(root, text='Start Processing', font=('Helvetica', 10, 'bold'), command=process_video,
                        justify=LEFT)

url_label.grid(sticky=W, row=1, column=0)
url_entry.grid(sticky=W, row=1, column=1)
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
