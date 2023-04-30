# Vimeo Uploader in AWS Lambda

[![Run Python Sanity for Lambda](https://github.com/davidjeong/vimeo-uploader/actions/workflows/lambda-python-sanity.yml/badge.svg?branch=main)](https://github.com/davidjeong/vimeo-uploader/actions/workflows/lambda-python-sanity.yml) [![Push Lambda Docker Image to ECR](https://github.com/davidjeong/vimeo-uploader/actions/workflows/lambda-docker-push-ecr.yml/badge.svg?branch=main)](https://github.com/davidjeong/vimeo-uploader/actions/workflows/lambda-docker-push-ecr.yml)

This is the sub-module containing backend functionalities required for downloading the video, performing video processing,
and re-upload to platform of choice. Initially, the video processing logic resided on the client side,
and required users to go through complicated setup with FFmpeg.

`AWS Lambda` will handle the invocations by the client side, and perform the necessary operations. `AWS Lambda` 
makes sense over deploying the backend service on `EC2` due to the nature of the usage of this tool (it is used very rarely).

We have two lambda functions
- `get-video-metadata` fetches the metadata about the YouTube video and returns it to the user. This is done
via [yt-dlp](https://github.com/yt-dlp/yt-dlp).
- `process-video` processes the video according to user input, and uploads the video to target platform
(and also S3 bucket if required).

## How this works
We package up all the necessary python scripts into a single docker image.
- `app.py` contains the entry point for all lambda functions.
- On the AWS console, we create a lambda function using image, but override the `CMD`.

## Configuration of Lambda Function
It is recommended that the following settings be used on `AWS Lambda`
- `get-video-metadata`
  - Memory of 2048MB (more ram = faster operation)
  - Ephemeral storage of 512MB
  - Time out of 1 minute
- `process-video`
  - Memory of 2048MB
  - Ephemeral storage of 6144MB (can be tuned according to video characteristics)
  - Timeout of 10 minutes

For `process-video` lambda function, the following ENV variables need to be set on function configuration section.
- `S3_THUMBNAIL_BUCKET_NAME`: Name of the thumbnail S3 Bucket
- `S3_VIDEO_BUCKET_NAME`: Name of the video S3 Bucket
- `VIMEO_CLIENT_KEY`: API client key for Vimeo
- `VIMEO_CLIENT_SECRET`: API client secret for Vimeo
- `VIMEO_CLIENT_TOKEN`: API client token for Vimeo

Furthermore, the appropriate IAM permissions are required to be set for authentication
for S3 upload.
