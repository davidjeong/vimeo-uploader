class VideoConfiguration:

    def __init__(self, video_url, start_time, end_time, resolution, video_title=None, image_url=None) -> None:
        """
        Initialize the video configuration object
        :param video_url: URL to video
        :param start_time: Start time of video in format 'HH:MM:SS'
        :param end_time: End time of video in seconds 'HH:MM:SS'
        :param resolution: Resolution of the video
        :param video_title: Title of the video
        :param image_url: URL to the thumbnail image
        """
        self.video_url = video_url
        self.start_time = start_time
        self.end_time = end_time
        self.resolution = resolution
        self.video_title = video_title
        self.image_url = image_url
