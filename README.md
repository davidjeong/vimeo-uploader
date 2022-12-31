# Vimeo Uploader

This is mono-repo consisting of the following sub-projects.
- [vimeo-uploader-lambda](https://github.com/davidjeong/vimeo-uploader/tree/main/vimeo-uploader-lambda) (backend scripts deployed onto `AWS Lambda` as Docker images)
- [vimeo-uploader-python](https://github.com/davidjeong/vimeo-uploader/tree/main/vimeo-uploader-python) (python-based client)
- [vimeo-uploader-swift](https://github.com/davidjeong/vimeo-uploader/tree/main/vimeo-uploader-swift) (mac-based client, still in-progress)

The goal of this is to allow users to 
- scrap videos from `YouTube`,
- trim the videos (or perform additional post-processing using `FFMpeg`),
- upload to `Vimeo` (or other platform via custom implementation)
