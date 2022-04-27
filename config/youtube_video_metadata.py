class YoutubeVideoMetadata:

    def __init__(self, video_id: str, title: str, author: str, length: int, publish_date: str):
        """
        Initialize the YouTube video metadata
        :param video_id: Id of video
        :param title: Title of video
        :param author: Author of video
        :param length: Length of video
        :param publish_date: Publish date string
        """
        self.video_id = video_id
        self.title = title
        self.author = author
        self.length = length
        self.publish_date = publish_date
