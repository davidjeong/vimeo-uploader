from abc import ABC, abstractmethod

import ffmpeg


class Transformation(ABC):

    @abstractmethod
    def apply(self, input_video_path: str, output_video_path) -> str:
        """
        Transform the video specified by the input path, to the output path.
        """
        pass


class TrimTransformation(Transformation):
    """
    Transformation involving trimming of videos from specified start to end timestamps.
    """

    def __init__(self, start_time_in_sec: int, end_time_in_sec: int):
        self.start_time_in_sec = start_time_in_sec
        self.end_time_in_sec = end_time_in_sec

    def apply(self, input_video_path: str, output_video_path: str) -> str:
        input_video = ffmpeg.input(input_video_path)
        ffmpeg.output(
            input_video,
            output_video_path,
            ss=self.start_time_in_sec,
            to=self.end_time_in_sec,
            vcodec='copy',
            acodec='copy').run()



