import shutil
from pathlib import Path
from typing import Optional


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_copy(src: Path, dst_dir: Path, new_name: str = None) -> Optional[Path]:
    if not src.exists():
        return None
    dst_dir = ensure_dir(dst_dir)
    dst = dst_dir / (new_name if new_name else src.name)
    shutil.copy2(str(src), str(dst))
    return dst


def safe_move(src: Path, dst_dir: Path, new_name: str = None) -> Optional[Path]:
    if not src.exists():
        return None
    dst_dir = ensure_dir(dst_dir)
    dst = dst_dir / (new_name if new_name else src.name)
    shutil.move(str(src), str(dst))
    return dst


def unique_filename(directory: Path, base_name: str, extension: str) -> Path:
    directory = ensure_dir(directory)
    counter = 1
    while True:
        if counter == 1:
            filename = f"{base_name}{extension}"
        else:
            filename = f"{base_name}_{counter}{extension}"
        path = directory / filename
        if not path.exists():
            return path
        counter += 1


def get_extension(filepath: Path) -> str:
    return filepath.suffix.lower()
