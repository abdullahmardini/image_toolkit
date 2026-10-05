from __future__ import annotations

from pathlib import Path

from PIL import Image
from rich.console import Console

from .. import constants
from ..core import files, images

console = Console()


def upscale_small() -> None:
    files.ensure_backup_dir()
    try:
        from realesrgan_ncnn_py import Realesrgan

        realesrgan = Realesrgan(gpuid=0, model=0)
    except ImportError:
        console.print(
            "realesrgan-ncnn-py not installed. Install with: uv pip install -e '.[upscale]' or pip install realesrgan-ncnn-py"
        )
        return
    except Exception as e:
        console.print(f"Real-ESRGAN unavailable: {e}")
        return

    allowed = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    for p in files.list_files(constants.TARGET_DIR):
        name = p.name
        if Path(name).suffix.lower() not in allowed:
            continue
        try:
            size_kb = p.stat().st_size / 1024.0
        except OSError:
            continue
        if size_kb > constants.MAX_SIZE_KB_UPSCALE:
            continue
        backup = files.safe_move_to_backup(p)
        try:
            with images.open_with_exif(backup) as img:
                img_rgb = img.convert("RGB")
                upscaled_img = realesrgan.process_pil(img_rgb)
                out_name = Path(name).stem + ".jpg"
                out_path = constants.TARGET_DIR / out_name
                upscaled_img.save(out_path, "JPEG", quality=95)
            console.print(f"Upscaled {name} -> {out_name}")
        except Exception as e:
            console.print(f"Error processing {name}: {e}")
            files.restore_backup(backup, name)
