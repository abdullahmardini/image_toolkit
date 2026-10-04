# /// script
# dependencies = [
#   "imageio-ffmpeg",
# ]
# ///

import os
import json
import shutil
import subprocess
import imageio_ffmpeg

BACKUP_DIR = "_backup_originals"
TARGET_DIR = os.getcwd()
VIDEO_EXTS = {".mov", ".mp4", ".mkv", ".webm"}


def probe_file(ffprobe_path: str, filepath: str) -> tuple[str | None, str | None]:
    cmd = [
        ffprobe_path,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        filepath,
    ]
    try:
        out = subprocess.check_output(cmd)
        data = json.loads(out)
        v_codec, a_codec = None, None
        for stream in data.get("streams", []):
            stype = stream.get("codec_type")
            if stype == "video" and not v_codec:
                v_codec = stream.get("codec_name")
            elif stype == "audio" and not a_codec:
                a_codec = stream.get("codec_name")
        return v_codec, a_codec
    except Exception:
        return None, None


def transcode_video(ffmpeg_path: str, src_path: str, dest_path: str):
    # Lanczos upscale filter + unsharp mask + 16:9 black bar padding
    vf_filter = (
        "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,"
        "unsharp=5:5:0.6:5:5:0.0,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
    )
    cmd = [
        ffmpeg_path,
        "-y",
        "-i",
        src_path,
        "-vf",
        vf_filter,
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "main",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-movflags",
        "+faststart",
        dest_path,
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed for {src_path}:\n{result.stderr}")


def main():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffprobe_exe = ffmpeg_exe.replace("ffmpeg", "ffprobe")
    os.makedirs(BACKUP_DIR, exist_ok=True)

    for item in os.listdir(TARGET_DIR):
        src_path = os.path.join(TARGET_DIR, item)
        if not os.path.isfile(src_path):
            continue

        ext = os.path.splitext(item)[1].lower()
        if ext not in VIDEO_EXTS:
            continue

        v_codec, a_codec = probe_file(ffprobe_exe, src_path)

        # Skip files that are already H.264 + AAC
        if v_codec in ["h264", "avc"] and a_codec in ["aac", None]:
            print(f"Skipping {item} (Already H.264/AAC)")
            continue

        backup_path = os.path.join(BACKUP_DIR, item)
        output_filename = os.path.splitext(item)[0] + ".mp4"
        dest_path = os.path.join(TARGET_DIR, output_filename)

        print(f"Processing {item} ({v_codec}) -> {output_filename}...")

        # Move original to backup directory first
        shutil.move(src_path, backup_path)

        try:
            transcode_video(ffmpeg_exe, backup_path, dest_path)
            print(f"Finished {item}")
        except Exception as e:
            print(f"Error processing {item}: {e}")
            # Restore original on failure
            if os.path.exists(backup_path) and not os.path.exists(src_path):
                shutil.move(backup_path, src_path)


if __name__ == "__main__":
    main()
