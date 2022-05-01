class VideoConfiguration:

    def __init__(self, video_id, start_time_in_sec, end_time_in_sec, resolution, video_title=None,
                 image_url=None) -> None:
        """
        Initialize the video configuration object
        :param video_id: Video ID
        :param start_time_in_sec: Start time of video in seconds
        :param end_time_in_sec: End time of video in seconds
        :param resolution: Resolution of the video
        :param video_title: Title of the video
        :param image_url: URL to the thumbnail image
        """
        self.video_id = video_id
        self.start_time_in_sec = start_time_in_sec
        self.end_time_in_sec = end_time_in_sec
        self.resolution = resolution
        self.video_title = video_title
        self.image_url = image_url
