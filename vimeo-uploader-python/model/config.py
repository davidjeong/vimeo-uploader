from dataclasses import dataclass


@dataclass
class AwsCredentials:
    """
    Data object for AWS credentials
    """
    aws_access_key_id: str
    aws_secret_access_key: str
