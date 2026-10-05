from __future__ import annotations

import subprocess
from pathlib import Path

import imageio_ffmpeg

from .. import constants


def ffmpeg_exe() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def transcode_to_1080p(src_path: Path, dest_path: Path) -> None:
    cmd = [
        ffmpeg_exe(),
        "-y",
        "-i",
        str(src_path),
        "-vf",
        constants.TRANS_VF,
        "-c:v",
        constants.TRANS_VCODEC,
        "-preset",
        constants.TRANS_PRESET,
        "-crf",
        constants.TRANS_CRF,
        "-pix_fmt",
        constants.TRANS_PIX_FMT,
        "-profile:v",
        constants.TRANS_PROFILE,
        "-c:a",
        constants.TRANS_ACODEC,
        "-b:a",
        constants.TRANS_ABIT,
        "-movflags",
        constants.TRANS_MOVFLAGS,
        str(dest_path),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed for {src_path}:\n{result.stderr}")
