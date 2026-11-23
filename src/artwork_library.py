"""Portable artwork files kept in the user's XDG configuration directory.

The GUI imports chosen .txt files into the `artworks/` folder. The renderer
continues to read the files from disk at launch, so scripts can update them.
This module deliberately doesn't depend on GTK.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ARTWORK_FOLDER = 'artworks'


def valid_artwork_reference(value: str) -> bool:
    """Allow legacy root .txt files and new `artworks/foo.txt` references."""
    if not isinstance(value, str) or '\x00' in value:
        return False
    value = value.strip()
    parts = Path(value).parts
    if len(parts) == 1:
        name = parts[0]
    elif len(parts) == 2 and parts[0] == ARTWORK_FOLDER:
        name = parts[1]
    else:
        return False
    return (bool(name) and name not in ('.', '..') and not name.startswith('.')
            and name.lower().endswith('.txt') and '\\' not in value
            and '/' not in name and name not in ('artworks',))


def import_artwork_file(source: Path, config_dir: Path) -> str:
    """Copy a selected .txt to the user's artwork library without overwriting.

    Returns a relative reference understood by the application and renderer.
    Existing files in `artworks/` are reused, not modified.
    """
    source = Path(source).expanduser().resolve(strict=True)
    if not source.is_file() or not valid_artwork_reference(source.name):
        raise ValueError('Choose a regular .txt artwork file.')
    if source.stat().st_size > 2_000_000:
        raise ValueError('Artwork is too large (maximum 2 MB).')
    destination = Path(config_dir).expanduser() / ARTWORK_FOLDER
    destination.mkdir(parents=True, exist_ok=True)
    dest_dir = destination.resolve(strict=True)
    if source.parent == dest_dir:
        return f'{ARTWORK_FOLDER}/{source.name}'
    name = source.name
    target = destination / name
    index = 2
    while target.exists():
        target = destination / f'{source.stem}-{index}{source.suffix}'
        index += 1
    # Exclusive create means a concurrent chooser cannot overwrite a user's file.
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst)
    return f'{ARTWORK_FOLDER}/{target.name}'


def artwork_filename_stem(name: str) -> str:
    """Portable and predictable display-name normalization for new assets."""
    import re
    import unicodedata
    label = str(name).strip()
    if label.lower().endswith('.txt'):
        label = label[:-4]
    ascii_name = unicodedata.normalize('NFKD', label).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9_-]+', '-', ascii_name.lower()).strip('-_')[:56] or 'photo-art'


def save_generated_artwork(config_dir: Path, name: str, text: str) -> str:
    """Safely create a new library asset, without overwriting other artworks.

    A display name is turned into a short, portable ASCII filename. We use
    exclusive creation rather than a check-then-write operation, including
    when a second export tries to claim the same filename simultaneously.
    """
    import os

    if not isinstance(text, str) or not text or '\x00' in text:
        raise ValueError('Artwork must contain nonempty text without NUL.')
    data = text.encode('utf-8')
    if len(data) > 2_000_000:
        raise ValueError('Artwork is too large (maximum 2 MB).')
    slug = artwork_filename_stem(name)
    root = Path(config_dir).expanduser().resolve(strict=True)
    folder = root / ARTWORK_FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    if folder.is_symlink() or folder.resolve(strict=True).parent != root:
        raise ValueError('Artwork directory must be inside the configuration folder.')
    for number in range(1, 10_001):
        suffix = '' if number == 1 else f'-{number}'
        filename = f'{slug}{suffix}.txt'
        target = folder / filename
        created = False
        try:
            with target.open('xb') as output:
                created = True
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            return f'{ARTWORK_FOLDER}/{filename}'
        except FileExistsError:
            continue
        except BaseException:
            # Delete only a file *we* created, never any pre-existing asset.
            if created:
                target.unlink(missing_ok=True)
            raise
    raise FileExistsError('Too many artworks with the same name.')
