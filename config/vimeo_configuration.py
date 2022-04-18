class VimeoConfiguration:

    def __init__(self, token, key, secret) -> None:
        """
        Initialize the vimeo configuration object
        :param token: Access token
        :param key: Client id
        :param secret: Client secret
        """
        self.token = token
        self.key = key
        self.secret = secret
