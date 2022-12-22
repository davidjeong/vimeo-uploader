class VimeoUploaderInternalServerError(Exception):
    """
    Generic internal server error thrown by service
    """


class VimeoUploaderInvalidVideoIdError(Exception):
    """
    Error thrown for video id not found
    """
