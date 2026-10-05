# Image Toolkit

A vibe coded toolkit for editing pictures

## Why
I have countless pictures and videos I want to load onto a digital picture frame.
These picture: 
* have inconsistent formats (thanks heic)
* have inconsistent orientation (thanks me) 
* may have poor quality

## Usage

Run in the directory containing images/videos:

- `itk audit` - Audit orientations/aspect ratios
- `itk copy` - Collect Photos-1-001* into CWD, HEIC->PNG, dedupe
- `itk downscale` - Downscale >10MB to 1920x1080 JPEG (backs up originals)
- `itk upscale` - AI-upscale <=100KB (backs up originals; needs `.[upscale]`)
- `itk transcode` - Transcode non-H.264/AAC videos to 1080p MP4 (backs up originals)
- `itk crop` - Interactive 9:16 portrait crop with YOLO cat centering

Install: `uv pip install -e .` (or `uv pip install -e '.[upscale]'`)
Run: `uv run itk ...`
