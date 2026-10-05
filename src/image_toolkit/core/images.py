from __future__ import annotations

from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

from .. import constants


def open_with_exif(path: Path) -> Image.Image:
    img = Image.open(path)
    img.load()
    if hasattr(Image, "ops"):
        try:
            img = Image.ops.exif_transpose(img)
        except Exception:
            pass
    return img


def classify_ratio(w: int, h: int) -> str:
    if h <= 0:
        return "Square (1:1)"
    ratio = w / h
    tol = constants.CROP_TOLERANCE
    if abs(ratio - (16.0 / 9.0)) < tol:
        return "16:9 Landscape (Native)"
    if abs(ratio - (9.0 / 16.0)) < tol:
        return "9:16 Portrait (Native)"
    if w > h:
        return "Other Landscape"
    if h > w:
        return "Other Portrait"
    return "Square (1:1)"


def is_non_portrait_9x16(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            img.load()
            if hasattr(Image, "ops"):
                try:
                    img = Image.ops.exif_transpose(img)
                except Exception:
                    pass
            w, h = img.size
            ratio = w / h if h > 0 else 1.0
            return abs(ratio - constants.PORTRAIT_ASPECT) >= constants.CROP_TOLERANCE
    except Exception:
        return False
