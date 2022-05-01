import os


class AppDirectoryConfiguration:

    vimeo_config_file_name = 'vimeo_config.yaml'

    def __init__(self, root_dir, videos_dir, config_dir):
        self.root_dir = root_dir
        self.videos_dir = videos_dir
        self.config_dir = config_dir

    def get_vimeo_config_file_path(self) -> str:
        return os.path.join(self.config_dir, self.vimeo_config_file_name)

    def get_new_video_directory(self) -> str:

        return os.path.join(self.config_dir, )
