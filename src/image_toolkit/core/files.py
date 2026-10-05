from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

from .. import constants


def ensure_backup_dir() -> Path:
    d = constants.backup_dir()
    d.mkdir(exist_ok=True)
    return d


def safe_move_to_backup(src: Path) -> Path:
    ensure_backup_dir()
    backup_path = constants.backup_dir() / src.name
    # If same exists, uniquify
    if backup_path.exists():
        stem = src.stem
        suffix = src.suffix
        i = 1
        while True:
            candidate = constants.backup_dir() / f"{stem}_{i}{suffix}"
            if not candidate.exists():
                backup_path = candidate
                break
            i += 1
    shutil.move(str(src), str(backup_path))
    return backup_path


def restore_backup(backup_path: Path, original_name: str) -> None:
    orig = constants.TARGET_DIR / original_name
    if backup_path.exists() and not orig.exists():
        shutil.move(str(backup_path), str(orig))


def move_with_dedupe(src: Path, filename: str, size: int, target_dir: Path, target_cache: dict) -> None:
    dest = target_dir / filename
    if src.resolve() == dest.resolve():
        return

    if not dest.exists():
        shutil.move(str(src), str(dest))
        target_cache[filename] = {"size": size, "hash": None, "path": str(dest)}
        return

    cached_info = target_cache.get(filename)
    dest_size = cached_info["size"] if cached_info else dest.stat().st_size

    if size == dest_size:
        src_hash = blake2b_hash(src)
        dest_hash = cached_info.get("hash") if cached_info else None
        if not dest_hash:
            dest_hash = blake2b_hash(dest)
            if cached_info:
                cached_info["hash"] = dest_hash
        if src_hash == dest_hash:
            try:
                src.unlink()
            except OSError:
                pass
            return

    counter = 1
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    while True:
        new_name = f"dup_{counter}_{stem}{suffix}"
        new_dest = target_dir / new_name
        if not new_dest.exists():
            shutil.move(str(src), str(new_dest))
            return
        new_size = new_dest.stat().st_size
        if size == new_size:
            src_hash = blake2b_hash(src)
            if src_hash == blake2b_hash(new_dest):
                try:
                    src.unlink()
                except OSError:
                    pass
                return
        counter += 1
        if counter > 10000:
            shutil.move(str(src), str(new_dest))
            return


def blake2b_hash(path: Path) -> str:
    h = hashlib.blake2b()
    with path.open("rb") as f:
        while chunk := f.read(128 * 1024):
            h.update(chunk)
    return h.hexdigest()


def is_image_file(name: str) -> bool:
    return Path(name).suffix.lower() in constants.IMAGE_EXTS


def is_video_file(name: str) -> bool:
    return Path(name).suffix.lower() in constants.VIDEO_EXTS


def is_video_trans_file(name: str) -> bool:
    return Path(name).suffix.lower() in constants.VIDEO_TRANS_EXTS


def list_files(target: Path) -> list[Path]:
    return [p for p in target.iterdir() if p.is_file()]
