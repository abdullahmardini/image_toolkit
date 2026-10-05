import os
from pathlib import Path

TARGET_DIR = Path.cwd()
BACKUP_DIR = Path("_backup_originals")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".heif", ".tiff"}
IMAGE_OUTPUT_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTS = {".mov", ".mp4", ".mkv", ".webm", ".avi"}
VIDEO_TRANS_EXTS = {".mov", ".mp4", ".mkv", ".webm"}

MIN_SIZE_MB_DOWNSCALE = 10.0
MAX_W_DOWNSCALE = 1920
MAX_H_DOWNSCALE = 1080
JPEG_QUALITY_DOWNSCALE = 90

MAX_SIZE_KB_UPSCALE = 100.0

PORTRAIT_ASPECT = 9.0 / 16.0
CROP_TOLERANCE = 0.02
CROP_SAVE_W = 1080
CROP_SAVE_H = 1920
CROP_SAVE_QUALITY = 90

TRANS_VF = (
    "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,"
    "unsharp=5:5:0.6:5:5:0.0,"
    "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
)

TRANS_VCODEC = "libx264"
TRANS_PRESET = "slow"
TRANS_CRF = "18"
TRANS_PIX_FMT = "yuv420p"
TRANS_PROFILE = "main"
TRANS_ACODEC = "aac"
TRANS_ABIT = "160k"
TRANS_MOVFLAGS = "+faststart"

YOLO_MODEL = "yolov8n.pt"
CAT_CLASS_ID = 15  # COCO cat

PHOTO_DIR_GLOB = "Photos-1-001*"

def cwd() -> Path:
    return Path.cwd()

def backup_dir() -> Path:
    return cwd() / BACKUP_DIR
