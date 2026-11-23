"""Offline creative conversion looks and safely persisted user photo presets.

The renderer and saved photo recipes remain PhotoSettings-based; presets only
apply controls, and never write or modify an artwork or its original image.
No GTK imports so every operation can be regression-tested headlessly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import unicodedata

from artwork_library import artwork_filename_stem
from photo_ascii import PhotoSettings
from photo_project import _validated_settings

PRESET_FOLDER = 'photo-presets'
FORMAT = 'ascii-saver-photo-preset'
VERSION = 1
MAX_PRESET_BYTES = 4096
MAX_NAME_LENGTH = 60
MAX_PRESETS = 100


@dataclass(frozen=True)
class ConversionPreset:
    key: str
    name: str
    description: str
    settings: PhotoSettings
    builtin: bool = False


# Distinct settings, not interchangeable layout templates. All use the same
# renderer-safe monochrome converter; users may further customize each look.
BUILTIN_PRESETS: tuple[ConversionPreset, ...] = (
    ConversionPreset('builtin/classic', 'Classic Terminal',
                     'Clean terminal typography with balanced detail.', PhotoSettings(), True),
    ConversionPreset('builtin/noir', 'Film Noir',
                     'Strong shadows and grain for dramatic portraits.',
                     PhotoSettings(columns=66, rows=34, contrast=160,
                                   brightness=-12, gamma=0.9, ramp='Fine detail',
                                   edge=35, dither=True), True),
    ConversionPreset('builtin/landscape', 'Soft Horizon',
                     'A wide, quiet landscape with gentle tonal transitions.',
                     PhotoSettings(columns=106, rows=27, fit='fit',
                                   contrast=90, brightness=6, gamma=1.2,
                                   ramp='Fine detail', dither=True), True),
    ConversionPreset('builtin/poster', 'Graphic Ink',
                     'Bold minimal shapes with poster-like contrast.',
                     PhotoSettings(columns=62, rows=30, contrast=190,
                                   ramp='Minimal', edge=65, posterize=3), True),
    ConversionPreset('builtin/arcade', '8-Bit Arcade',
                     'Chunky characters and punchy retro-game artwork.',
                     PhotoSettings(columns=42, rows=23, contrast=150,
                                   ramp='Minimal', dither=False, posterize=4), True),
    ConversionPreset('builtin/blueprint', 'Architectural Detail',
                     'Fine edges for buildings, objects and structures.',
                     PhotoSettings(columns=110, rows=43, contrast=125,
                                   ramp='Fine detail', edge=85, dither=False), True),
)


def _root(config_dir: Path) -> Path:
    return Path(config_dir).expanduser().resolve(strict=True)


def _folder(root: Path, *, create: bool = False) -> Path:
    folder = root / PRESET_FOLDER
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise ValueError('Preset directory must be a regular directory.')
    if create:
        folder.mkdir(mode=0o700, exist_ok=True)
    if folder.exists() and folder.resolve(strict=True).parent != root:
        raise ValueError('Preset directory is outside the configuration root.')
    return folder


def _name(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError('Preset name must be text.')
    name = unicodedata.normalize('NFC', value.strip())
    if (not name or len(name) > MAX_NAME_LENGTH or
            any(ord(c) < 32 or ord(c) == 127 for c in name)):
        raise ValueError('Enter a preset name (1–60 characters, no controls).')
    return name


def _path(root: Path, key: str) -> Path:
    if (not isinstance(key, str) or not key.startswith('custom/') or
            len(key) > 100 or '\\' in key):
        raise ValueError('Not a saved custom preset.')
    slug = key.removeprefix('custom/')
    if (not slug or slug.startswith('.') or '/' in slug or
            any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in slug)):
        raise ValueError('Invalid preset key.')
    return _folder(root) / f'{slug}.json'


def _read(root: Path, key: str) -> ConversionPreset:
    path = _path(root, key)
    if (path.is_symlink() or not path.is_file() or
            not 0 < path.stat().st_size <= MAX_PRESET_BYTES):
        raise ValueError('Preset file is missing or invalid.')
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Corrupt preset JSON.') from exc
    if (not isinstance(raw, dict) or set(raw) != {'format', 'version', 'name', 'settings'}
            or raw['format'] != FORMAT or type(raw['version']) is not int
            or raw['version'] != VERSION):
        raise ValueError('Unsupported preset format.')
    return ConversionPreset(key, _name(raw['name']), 'Saved personal look',
                            _validated_settings(raw['settings']))


def list_presets(config_dir: Path) -> tuple[list[ConversionPreset], int]:
    """Curated looks first, then valid local presets; count malformed files."""
    root = _root(config_dir)
    folder = _folder(root)
    results = list(BUILTIN_PRESETS)
    skipped = 0
    if not folder.exists():
        return results, skipped
    for file in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
        if file.suffix != '.json':
            continue
        try:
            preset = _read(root, f'custom/{file.stem}')
        except (ValueError, OSError):
            skipped += 1
            continue
        results.append(preset)
    return results, skipped


def save_preset(config_dir: Path, name: str, settings: PhotoSettings) -> ConversionPreset:
    """Create, never replace, a named preset with the current valid settings."""
    title = _name(name)
    if not isinstance(settings, PhotoSettings):
        raise ValueError('Invalid photo conversion settings.')
    settings.validate()
    root = _root(config_dir)
    folder = _folder(root, create=True)
    # Names shown by the picker should be unambiguous; never silently make a
    # second look with the same visible title.
    existing, _skipped = list_presets(root)
    if any(preset.name.casefold() == title.casefold() for preset in existing):
        raise ValueError('That preset name is already in use. Choose another name.')
    if len([file for file in folder.iterdir() if file.suffix == '.json']) >= MAX_PRESETS:
        raise ValueError('The personal preset library is full (100 presets).')
    slug = artwork_filename_stem(title)
    if not slug or slug == 'photo-art' and not any(c.isalnum() for c in title):
        raise ValueError('Preset name must contain letters or digits.')
    for index in range(1, MAX_PRESETS + 2):
        stem = slug if index == 1 else f'{slug}-{index}'
        key = 'custom/' + stem
        target = _path(root, key)
        payload = (json.dumps({'format': FORMAT, 'version': VERSION,
                               'name': title, 'settings': asdict(settings)},
                              ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
        if len(payload) > MAX_PRESET_BYTES:
            raise ValueError('Preset is too large.')
        created = False
        try:
            # 'xb' prevents accidental overwrite even after name collisions.
            with target.open('xb') as output:
                created = True
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            return ConversionPreset(key, title, 'Saved personal look', settings)
        except FileExistsError:
            continue
        except BaseException:
            if created:
                target.unlink(missing_ok=True)
            raise
    raise FileExistsError('Too many presets with the same name.')


def delete_preset(config_dir: Path, key: str) -> None:
    """Delete only one validated personal preset. Built-ins cannot be deleted."""
    root = _root(config_dir)
    path = _path(root, key)
    _read(root, key)  # Validate identity and reject symlinks/invalid metadata.
    path.unlink()
