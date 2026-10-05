from __future__ import annotations

import typer
from rich.console import Console

from .commands import audit, copy, crop, downscale, transcode, upscale

app = typer.Typer(help="Image Toolkit CLI (itk)")
console = Console()


@app.command("audit")
def audit_cmd() -> None:
    """Audit image/video orientations and aspect ratios in current directory."""
    audit.audit()


@app.command("copy")
def copy_cmd() -> None:
    """Collect Photos-1-001* images into CWD, convert HEIC->PNG, dedupe by hash/size."""
    copy.copy_photos()


@app.command("downscale")
def downscale_cmd() -> None:
    """Downscale images > 10 MB to max 1920x1080 JPEG (backs up originals)."""
    downscale.downscale_large()


@app.command("upscale")
def upscale_cmd() -> None:
    """AI-upscale images <= 100 KB via Real-ESRGAN (backs up originals)."""
    upscale.upscale_small()


@app.command("transcode")
def transcode_cmd() -> None:
    """Transcode non-H.264/AAC videos to 1080p H.264/AAC MP4 (backs up originals)."""
    transcode.transcode_videos()


@app.command("crop")
def crop_cmd() -> None:
    """Interactive 9:16 portrait crop (YOLOv8n cat auto-centering)."""
    crop.crop_portrait()


if __name__ == "__main__":
    app()
