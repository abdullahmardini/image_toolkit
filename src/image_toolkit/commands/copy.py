from __future__ import annotations

import glob
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console

from .. import constants
from ..core import files
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

console = Console()


def _process_file(src_path_str: str, filename: str) -> tuple[str, str, int] | None:
    src = Path(src_path_str)
    ext = Path(filename).suffix.lower()
    if ext in (".heic", ".heif"):
        try:
            new_filename = Path(filename).stem + ".png"
            temp_png = src.with_suffix(src.suffix + ".tmp.png")
            with Image.open(src) as img:
                img.save(temp_png, format="PNG", compress_level=1)
            if src.exists():
                try:
                    src.unlink()
                except OSError:
                    pass
            src = temp_png
            filename_out = new_filename
        except Exception as e:
            console.print(f"Error converting {src}: {e}")
            return None
    else:
        filename_out = filename
    size = src.stat().st_size
    return (str(src), filename_out, size)


def collect_photos_dirs(target_dir: Path) -> list[Path]:
    dirs = []
    for pattern in glob.glob(constants.PHOTO_DIR_GLOB):
        d = Path(pattern)
        if d.is_dir() and d.resolve() != target_dir.resolve():
            dirs.append(d)
    return dirs


def copy_photos() -> None:
    target_dir = constants.TARGET_DIR
    tasks: list[tuple[str, str]] = []
    for d in collect_photos_dirs(target_dir):
        for root, _, files_list in os.walk(d):
            r = Path(root)
            for f in files_list:
                if files.is_image_file(f):
                    sp = r / f
                    tasks.append((str(sp), f))
    if not tasks:
        console.print("No photo files found.")
        return

    target_cache: dict = {}
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 1) as executor:
        futures = [executor.submit(_process_file, sp, fn) for sp, fn in tasks]
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                src_s, fn_out, sz = res
                files.move_with_dedupe(Path(src_s), fn_out, sz, target_dir, target_cache)
    console.print("Copy/dedupe complete.")
