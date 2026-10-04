# /// script
# dependencies = [
#   "pillow",
#   "imageio-ffmpeg",
# ]
# ///

import os
import json
import subprocess
from collections import Counter
from PIL import Image
import imageio_ffmpeg

TARGET_DIR = os.getcwd()
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".tiff"}
VIDEO_EXTS = {".mov", ".mp4", ".mkv", ".webm", ".avi"}


def get_video_dimensions(ffprobe_path: str, filepath: str) -> tuple[int, int] | None:
    cmd = [
        ffprobe_path,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        filepath,
    ]
    try:
        out = subprocess.check_output(cmd)
        data = json.loads(out)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                width = int(stream.get("width", 0))
                height = int(stream.get("height", 0))

                # Check for rotation metadata (common in smartphone videos)
                side_data = stream.get("side_data_list", [])
                rotation = 0
                for sd in side_data:
                    if "rotation" in sd:
                        rotation = abs(int(sd["rotation"]))
                        break

                # Swap width and height if rotated 90 or 270 degrees
                if rotation in (90, 270):
                    width, height = height, width

                if width > 0 and height > 0:
                    return width, height
    except Exception:
        pass
    return None


def main():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffprobe_exe = ffmpeg_exe.replace("ffmpeg", "ffprobe")

    image_counts = Counter()
    video_counts = Counter()

    total_images = 0
    total_videos = 0

    print("Auditing directory media...")

    for item in os.listdir(TARGET_DIR):
        src_path = os.path.join(TARGET_DIR, item)
        if not os.path.isfile(src_path):
            continue

        ext = os.path.splitext(item)[1].lower()

        # Process Images
        if ext in IMAGE_EXTS:
            try:
                with Image.open(src_path) as img:
                    img = (
                        Image.ops.exif_transpose(img) if hasattr(Image, "ops") else img
                    )
                    w, h = img.size
                    total_images += 1

                    ratio = w / h
                    if abs(ratio - (16 / 9)) < 0.02:
                        image_counts["16:9 Landscape (Native)"] += 1
                    elif abs(ratio - (9 / 16)) < 0.02:
                        image_counts["9:16 Portrait (Native)"] += 1
                    elif w > h:
                        image_counts["Other Landscape"] += 1
                    elif h > w:
                        image_counts["Other Portrait"] += 1
                    else:
                        image_counts["Square (1:1)"] += 1
            except Exception:
                continue

        # Process Videos
        elif ext in VIDEO_EXTS:
            dims = get_video_dimensions(ffprobe_exe, src_path)
            if dims:
                w, h = dims
                total_videos += 1
                ratio = w / h
                if abs(ratio - (16 / 9)) < 0.02:
                    video_counts["16:9 Landscape (Native)"] += 1
                elif abs(ratio - (9 / 16)) < 0.02:
                    video_counts["9:16 Portrait (Native)"] += 1
                elif w > h:
                    video_counts["Other Landscape"] += 1
                elif h > w:
                    video_counts["Other Portrait"] += 1
                else:
                    video_counts["Square (1:1)"] += 1

    print("\n" + "=" * 45)
    print("           MEDIA AUDIT SUMMARY")
    print("=" * 45)

    print(f"\nIMAGES (Total: {total_images})")
    for category, count in image_counts.most_common():
        pct = (count / total_images * 100) if total_images else 0
        print(f"  • {category:<25}: {count:>5} ({pct:>5.1f}%)")

    print(f"\nVIDEOS (Total: {total_videos})")
    for category, count in video_counts.most_common():
        pct = (count / total_videos * 100) if total_videos else 0
        print(f"  • {category:<25}: {count:>5} ({pct:>5.1f}%)")

    print("=" * 45)


if __name__ == "__main__":
    main()
