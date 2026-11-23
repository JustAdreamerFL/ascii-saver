"""Testable, lossless artwork file read/write used by the built-in editor."""
from __future__ import annotations
import os
import tempfile
from pathlib import Path


def read_artwork(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def save_artwork(path: Path, text: str) -> None:
    """Atomically overwrite an existing artwork without escaping its directory."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    fd, temp_name = tempfile.mkstemp(prefix=".artwork-", dir=path.parent)
    temp = Path(temp_name)
    try:
        os.fchmod(fd, path.stat().st_mode & 0o777)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def editor_close_message(saved_count: int, discarded_edits: bool) -> str:
    """Only describe actions that actually happened to the artwork file."""
    if saved_count:
        return ("Artwork saved. Later unsaved edits discarded."
                if discarded_edits else "Artwork saved.")
    if discarded_edits:
        return "Unsaved artwork edits discarded."
    return "Artwork editor closed without changes."
