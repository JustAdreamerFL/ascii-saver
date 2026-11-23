"""Bounded, private history of artwork actually launched by the renderer.

Only local config-owned .txt assets are recorded; no paths leave the config root.
No GTK import and no synchronous writes per frame or effect when art is unchanged.
"""
from __future__ import annotations
from pathlib import Path
import json
import os
import tempfile
from time import time

HISTORY_NAME = 'artwork-history.json'
MAX_RECENT = 40
MAX_BYTES = 24_000

def history_path(config_dir):
    return Path(config_dir) / HISTORY_NAME

def read_history(config_dir):
    target = history_path(config_dir)
    if target.is_symlink() or not target.is_file():
        return []
    try:
        if target.stat().st_size > MAX_BYTES:
            return []
        raw = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError):
        return []
    result = []
    for entry in raw.get('recent', [])[:MAX_RECENT] if isinstance(raw, dict) else []:
        ref = entry.get('artwork') if isinstance(entry, dict) else None
        if (isinstance(ref, str) and (ref == 'logo.txt' or
            (ref.startswith('artworks/') and ref.count('/') == 1 and ref.endswith('.txt') and
             ref.split('/')[-1] not in ('', '.', '..')))
                and ref not in result):
            result.append(ref)
    return result

def remember_artwork(config_dir, artwork, *, timestamp=None):
    root = Path(config_dir).resolve()
    selected = Path(artwork)
    if selected.is_symlink() or not selected.is_file() or selected.suffix.lower() != '.txt':
        return False
    try:
        relative = selected.resolve(strict=True).relative_to(root).as_posix()
    except (OSError, ValueError):
        return False
    if relative != 'logo.txt' and not (relative.startswith('artworks/') and relative.count('/') == 1):
        return False
    history = read_history(root)
    if history and history[0] == relative:
        return False
    latest = [relative, *(item for item in history if item != relative)][:MAX_RECENT]
    target = history_path(root)
    if target.is_symlink():
        return False
    content = json.dumps({'version': 1, 'recent': [{'artwork': key} for key in latest]},
                         separators=(',', ':')).encode('utf-8')
    fd, temp = tempfile.mkstemp(prefix='.artwork-history-', dir=root)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, 0o600)
        if target.is_symlink():
            return False
        os.replace(temp, target)
    finally:
        Path(temp).unlink(missing_ok=True)
    return True
