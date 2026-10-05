from __future__ import annotations

from pathlib import Path

from rich.console import Console

from .. import constants
from ..core import ffmpeg, files, videos

console = Console()


def transcode_videos() -> None:
    files.ensure_backup_dir()
    for p in files.list_files(constants.TARGET_DIR):
        name = p.name
        if not files.is_video_trans_file(name):
            continue
        v_codec, a_codec = videos.video_codecs(p)
        if v_codec in ("h264", "avc") and a_codec in ("aac", None):
            console.print(f"Skipping {name} (Already H.264/AAC)")
            continue
        backup = files.safe_move_to_backup(p)
        try:
            out_name = Path(name).stem + ".mp4"
            out_path = constants.TARGET_DIR / out_name
            ffmpeg.transcode_to_1080p(backup, out_path)
            console.print(f"Transcoded {name} -> {out_name}")
        except Exception as e:
            console.print(f"Error processing {name}: {e}")
            files.restore_backup(backup, name)
