# /// script
# dependencies = [
#   "realesrgan-ncnn-py",
#   "pillow",
# ]
# ///

import os
import shutil
from PIL import Image
from realesrgan_ncnn_py import Realesrgan

# Configuration parameters
MAX_FILE_SIZE_KB = 100  # Threshold in KB to process
TARGET_DIR = os.getcwd()
BACKUP_DIR = "_backup_originals"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Initialize Real-ESRGAN model (gpuid=0 for GPU, model=0 for default x4 model)
    realesrgan = Realesrgan(gpuid=0, model=0)

    for item in os.listdir(TARGET_DIR):
        src_path = os.path.join(TARGET_DIR, item)
        if not os.path.isfile(src_path):
            continue

        ext = os.path.splitext(item)[1].lower()
        if ext not in IMAGE_EXTS:
            continue

        file_size_kb = os.path.getsize(src_path) / 1024
        if file_size_kb > MAX_FILE_SIZE_KB:
            continue

        backup_path = os.path.join(BACKUP_DIR, item)
        output_filename = os.path.splitext(item)[0] + ".jpg"
        dest_path = os.path.join(TARGET_DIR, output_filename)

        print(f"AI Upscaling {item} ({file_size_kb:.1f} KB)...")

        # Move original to backup directory first
        shutil.move(src_path, backup_path)

        try:
            with Image.open(backup_path) as img:
                img_rgb = img.convert("RGB")
                upscaled_img = realesrgan.process_pil(img_rgb)
                upscaled_img.save(dest_path, "JPEG", quality=95)
            print(f"Finished {item}")
        except Exception as e:
            print(f"Error processing {item}: {e}")
            # Restore original on failure
            if os.path.exists(backup_path) and not os.path.exists(src_path):
                shutil.move(backup_path, src_path)


if __name__ == "__main__":
    main()
