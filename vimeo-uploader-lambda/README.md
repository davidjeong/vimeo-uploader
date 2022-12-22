# Vimeo Uploader in AWS Lambda

[![Run Python Sanity for Lambda](https://github.com/davidjeong/vimeo-uploader/actions/workflows/lambda-python-sanity.yml/badge.svg?branch=main)](https://github.com/davidjeong/vimeo-uploader/actions/workflows/lambda-python-sanity.yml)[![Push Lambda Docker Image to ECR](https://github.com/davidjeong/vimeo-uploader/actions/workflows/lambda-docker-push-ecr.yml/badge.svg?branch=main)](https://github.com/davidjeong/vimeo-uploader/actions/workflows/lambda-docker-push-ecr.yml)

This is the repository containing python and docker files for the backend functionalities required by vimeo upload tool.
This is being migrated from [Vimeo Uploader](https://github.com/davidjeong/vimeo_uploader), which currently performs
all post-processing operations on the client side.

`AWS Lambda` will handle the invocations by the client side, and perform the necessary operations. `Lambda` was chosen over
`Amazon EC2` as this tool is used very rarely, and we do not want to instantiate `EC2` containers every time we need to use the
tool.

## How this works
Basically we package up all the necessary python scripts into
a single docker image.
- `app.py` contains the entry point for all lambda functions.
- On the AWS console, we create a lambda function using image, but override the `CMD`.