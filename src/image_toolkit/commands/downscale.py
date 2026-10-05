from __future__ import annotations

from pathlib import Path

from PIL import Image
from rich.console import Console

from .. import constants
from ..core import files, images

console = Console()


def downscale_large() -> None:
    files.ensure_backup_dir()
    for p in files.list_files(constants.TARGET_DIR):
        name = p.name
        if not files.is_image_file(name):
            continue
        try:
            size_mb = p.stat().st_size / (1024 * 1024)
        except OSError:
            continue
        if size_mb < constants.MIN_SIZE_MB_DOWNSCALE:
            continue
        backup = files.safe_move_to_backup(p)
        try:
            with images.open_with_exif(backup) as img:
                img_rgb = img.convert("RGB")
                img_rgb.thumbnail(
                    (constants.MAX_W_DOWNSCALE, constants.MAX_H_DOWNSCALE),
                    Image.Resampling.LANCZOS,
                )
                out_name = Path(name).stem + ".jpg"
                out_path = constants.TARGET_DIR / out_name
                img_rgb.save(
                    out_path,
                    "JPEG",
                    quality=constants.JPEG_QUALITY_DOWNSCALE,
                    optimize=True,
                )
            new_mb = out_path.stat().st_size / (1024 * 1024) if out_path.exists() else 0.0
            console.print(f"Downscaled {name} -> {out_name} ({new_mb:.2f} MB)")
        except Exception as e:
            console.print(f"Error processing {name}: {e}")
            files.restore_backup(backup, name)
