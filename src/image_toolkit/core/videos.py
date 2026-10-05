from __future__ import annotations

import json
import subprocess
from pathlib import Path

import imageio_ffmpeg


def ffprobe_exe() -> str:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    return ffmpeg_exe.replace("ffmpeg", "ffprobe")


def video_dimensions(path: Path) -> tuple[int, int] | None:
    fp = ffprobe_exe()
    cmd = [
        fp,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        str(path),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        data = json.loads(out)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                width = int(stream.get("width", 0))
                height = int(stream.get("height", 0))
                side_data = stream.get("side_data_list", [])
                rotation = 0
                for sd in side_data:
                    if "rotation" in sd:
                        try:
                            rotation = abs(int(sd["rotation"]))
                        except Exception:
                            pass
                        break
                if rotation in (90, 270):
                    width, height = height, width
                if width > 0 and height > 0:
                    return width, height
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
        return None


def video_codecs(path: Path) -> tuple[str | None, str | None]:
    fp = ffprobe_exe()
    cmd = [
        fp,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        str(path),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        data = json.loads(out)
        v_codec, a_codec = None, None
        for stream in data.get("streams", []):
            stype = stream.get("codec_type")
            if stype == "video" and not v_codec:
                v_codec = stream.get("codec_name")
            elif stype == "audio" and not a_codec:
                a_codec = stream.get("codec_name")
        return v_codec, a_codec
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
        return None, None
