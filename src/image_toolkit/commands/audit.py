from __future__ import annotations

from collections import Counter

from rich.console import Console
from rich.table import Table

from .. import constants
from ..core import files, images, videos

console = Console()


def audit() -> None:
    image_counts: Counter[str] = Counter()
    video_counts: Counter[str] = Counter()
    total_images = 0
    total_videos = 0

    console.print("Auditing directory media...")

    for p in files.list_files(constants.TARGET_DIR):
        name = p.name
        if files.is_image_file(name):
            try:
                with images.open_with_exif(p) as img:
                    w, h = img.size
                total_images += 1
                image_counts[images.classify_ratio(w, h)] += 1
            except (OSError, ValueError):
                continue
        elif files.is_video_file(name):
            dims = videos.video_dimensions(p)
            if dims:
                w, h = dims
                total_videos += 1
                video_counts[images.classify_ratio(w, h)] += 1

    table = Table(title="MEDIA AUDIT SUMMARY", show_lines=False)
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Pct %", justify="right")

    table.add_section()
    table.add_row(f"IMAGES (Total: {total_images})", "", "")
    for cat, count in image_counts.most_common():
        pct = (count / total_images * 100.0) if total_images else 0.0
        table.add_row(f"  {cat}", str(count), f"{pct:>5.1f}")

    table.add_section()
    table.add_row(f"VIDEOS (Total: {total_videos})", "", "")
    for cat, count in video_counts.most_common():
        pct = (count / total_videos * 100.0) if total_videos else 0.0
        table.add_row(f"  {cat}", str(count), f"{pct:>5.1f}")

    console.print(table)
