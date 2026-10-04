# /// script
# dependencies = [
#   "pillow",
#   "pillow-heif",
# ]
# ///

import os
import glob
import shutil
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()


def process_file(src, filename, target_dir):
    ext = os.path.splitext(filename)[1].lower()

    if ext in (".heic", ".heif"):
        try:
            filename = os.path.splitext(filename)[0] + ".png"
            temp_png = src + ".tmp.png"
            with Image.open(src) as img:
                img.save(temp_png, format="PNG", compress_level=1)
            if src != temp_png:
                os.remove(src)
            src = temp_png
        except Exception as e:
            print(f"Error converting {src}: {e}")
            return None

    size = os.path.getsize(src)
    return (src, filename, size)


def quick_hash(filepath):
    h = hashlib.blake2b()
    with open(filepath, "rb") as f:
        while chunk := f.read(128 * 1024):
            h.update(chunk)
    return h.hexdigest()


def move_to_target(src, filename, size, target_dir, target_cache):
    dest = os.path.join(target_dir, filename)
    if src == dest:
        return

    if not os.path.exists(dest):
        shutil.move(src, dest)
        target_cache[filename] = {"size": size, "hash": None, "path": dest}
        return

    cached_info = target_cache.get(filename)
    dest_size = cached_info["size"] if cached_info else os.path.getsize(dest)

    if size == dest_size:
        src_hash = quick_hash(src)
        dest_hash = cached_info.get("hash") if cached_info else None
        if not dest_hash:
            dest_hash = quick_hash(dest)
            if cached_info:
                cached_info["hash"] = dest_hash

        if src_hash == dest_hash:
            os.remove(src)
            return

    counter = 1
    new_dest = os.path.join(target_dir, f"dup_{counter}_{filename}")
    while os.path.exists(new_dest):
        new_size = os.path.getsize(new_dest)
        if size == new_size:
            src_hash = quick_hash(src)
            if src_hash == quick_hash(new_dest):
                os.remove(src)
                return
        counter += 1
        new_dest = os.path.join(target_dir, f"dup_{counter}_{filename}")

    shutil.move(src, new_dest)


def main():
    image_exts = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".heic",
        ".heif",
        ".tiff",
    }
    target_dir = os.getcwd()
    dirs = glob.glob("Photos-1-001*")

    tasks = []
    for d in dirs:
        if not os.path.isdir(d) or os.path.abspath(d) == target_dir:
            continue
        for root, _, files in os.walk(d):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in image_exts:
                    src_path = os.path.abspath(os.path.join(root, file))
                    tasks.append((src_path, file, target_dir))

    target_cache = {}

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_file, *t) for t in tasks]
        for future in as_completed(futures):
            res = future.result()
            if res:
                src, filename, size = res
                move_to_target(src, filename, size, target_dir, target_cache)


if __name__ == "__main__":
    main()
