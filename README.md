# Vimeo Uploader

This is mono-repo consisting of the following sub-projects.
- [vimeo-uploader-lambda](https://github.com/davidjeong/vimeo-uploader/tree/main/vimeo-uploader-lambda) (backend scripts deployed onto `AWS Lambda` as Docker images)
- [vimeo-uploader-swift](https://github.com/davidjeong/vimeo-uploader/tree/main/vimeo-uploader-swift) (mac-based client)

The goal of this is to allow users to 
- scrape videos from `YouTube`, perform post-processing via `yt-dlp` post-processor,
- upload to `Vimeo` (or other platform via custom implementation)
