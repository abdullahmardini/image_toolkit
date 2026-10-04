# /// script
# dependencies = [
#   "pillow",
# ]
# ///

import os
import shutil
from PIL import Image

# Configuration parameters
MIN_FILE_SIZE_MB = 10  # Threshold in MB to process
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
JPEG_QUALITY = 90

TARGET_DIR = os.getcwd()
BACKUP_DIR = "_backup_originals"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    for item in os.listdir(TARGET_DIR):
        src_path = os.path.join(TARGET_DIR, item)
        if not os.path.isfile(src_path):
            continue

        ext = os.path.splitext(item)[1].lower()
        if ext not in IMAGE_EXTS:
            continue

        file_size_mb = os.path.getsize(src_path) / (1024 * 1024)
        if file_size_mb < MIN_FILE_SIZE_MB:
            continue

        backup_path = os.path.join(BACKUP_DIR, item)
        output_filename = os.path.splitext(item)[0] + ".jpg"
        dest_path = os.path.join(TARGET_DIR, output_filename)

        print(f"Downscaling {item} ({file_size_mb:.1f} MB)...")

        # Move original to backup directory first
        shutil.move(src_path, backup_path)

        try:
            with Image.open(backup_path) as img:
                # Handle orientation metadata if present
                img = Image.ops.exif_transpose(img) if hasattr(Image, "ops") else img
                img_rgb = img.convert("RGB")

                # Scale image down while retaining aspect ratio
                img_rgb.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

                # Save optimized JPEG
                img_rgb.save(dest_path, "JPEG", quality=JPEG_QUALITY, optimize=True)

            new_size_mb = os.path.getsize(dest_path) / (1024 * 1024)
            print(f"Finished {item} -> {output_filename} ({new_size_mb:.2f} MB)")
        except Exception as e:
            print(f"Error processing {item}: {e}")
            # Restore original on failure
            if os.path.exists(backup_path) and not os.path.exists(src_path):
                shutil.move(backup_path, src_path)


if __name__ == "__main__":
    main()
