"""Self-contained, versioned photo-to-ASCII recipes for editable local artwork.

Renderer assets remain plain artworks/<name>.txt.  An opt-in sidecar folder
photo-projects/<name>/ holds an immutable copy of the source image and the
validated parameters used to render that text. No external path or command is
persisted. Creating a new project never overwrites any existing artwork.

This module contains no GTK dependencies and is safe to test headlessly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil

from artwork_library import ARTWORK_FOLDER, artwork_filename_stem, valid_artwork_reference
from photo_ascii import PhotoSettings

PROJECT_FOLDER = 'photo-projects'
PROJECT_FORMAT = 'ascii-saver-photo'
PROJECT_VERSION = 1
SOURCE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
MAX_SOURCE_BYTES = 25_000_000
MAX_TEXT_BYTES = 2_000_000
MAX_MANIFEST_BYTES = 8192


@dataclass(frozen=True)
class SavedPhotoProject:
    reference: str
    source_path: Path
    settings: PhotoSettings
    text_modified: bool


def _root(config_dir: Path) -> Path:
    return Path(config_dir).expanduser().resolve(strict=True)


def _directory(root: Path, name: str) -> Path:
    folder = root / name
    # Do not create through a symlink, even one pointing back inside the root.
    if folder.is_symlink():
        raise ValueError(f'{name} cannot be a symlink.')
    folder.mkdir(mode=0o700, exist_ok=True)
    if folder.resolve(strict=True).parent != root:
        raise ValueError(f'{name} is outside the configuration directory.')
    return folder


def _project_location(root: Path, reference: str) -> Path:
    if not valid_artwork_reference(reference) or not reference.startswith(ARTWORK_FOLDER + '/'):
        raise ValueError('Not a managed artwork reference.')
    stem = Path(reference).stem
    if not stem or stem.startswith('.'):
        raise ValueError('Invalid artwork name.')
    return root / PROJECT_FOLDER / stem


def reference_for_artwork(config_dir: Path, path: Path) -> str | None:
    """Return a stored conversion reference for a managed artwork file, if any."""
    try:
        root = _root(config_dir)
        file = Path(path)
        if file.is_symlink() or not file.is_file():
            return None
        relative = file.resolve(strict=True).relative_to(root).as_posix()
        location = _project_location(root, relative)
        if location.is_symlink() or not (location / 'project.json').is_file():
            return None
        return relative
    except (OSError, ValueError):
        return None


def _validated_settings(raw: object) -> PhotoSettings:
    expected = {f.name for f in fields(PhotoSettings)}
    # Older recipes lack V93 finishing tools and V94 custom ramp.
    # Only these fields may be absent. Unknown keys or missing core fields
    # remain invalid, rather than silently discarding a damaged recipe.
    optional = {'posterize', 'alpha_background', 'custom_ramp'}
    if (not isinstance(raw, dict) or not set(raw) <= expected
            or not (expected - optional) <= set(raw)):
        raise ValueError('Unknown or missing photo settings.')
    defaults = PhotoSettings()
    for name, value in raw.items():
        default = getattr(defaults, name)
        if isinstance(default, bool):
            if not isinstance(value, bool):
                raise ValueError(f'Invalid {name} setting.')
        elif isinstance(default, int):
            if type(value) is not int:
                raise ValueError(f'Invalid {name} setting.')
        elif isinstance(default, float):
            if type(value) not in (int, float):
                raise ValueError(f'Invalid {name} setting.')
        elif not isinstance(value, str):
            raise ValueError(f'Invalid {name} setting.')
    opts = PhotoSettings(**raw)
    opts.validate()
    return opts


def save_photo_project(config_dir: Path, name: str, text: str,
                       image_bytes: bytes, extension: str,
                       settings: PhotoSettings) -> str:
    """Create a fresh renderer .txt and matching editable source project.

    Each candidate reserves a private project directory, then publishes its
    output file with exclusive create. Failures roll back *our* own files and
    never overwrite or truncate an existing asset.
    """
    if not isinstance(text, str) or not text or '\x00' in text:
        raise ValueError('Invalid ASCII artwork.')
    encoded = text.encode('utf-8')
    if len(encoded) > MAX_TEXT_BYTES:
        raise ValueError('Artwork exceeds 2 MB.')
    if not isinstance(image_bytes, bytes) or not 0 < len(image_bytes) <= MAX_SOURCE_BYTES:
        raise ValueError('Source photo is missing or exceeds 25 MB.')
    if extension not in SOURCE_EXTENSIONS:
        raise ValueError('Unsupported image extension.')
    if not isinstance(settings, PhotoSettings):
        raise ValueError('Invalid conversion settings.')
    settings.validate()
    root = _root(config_dir)
    artwork_dir = _directory(root, ARTWORK_FOLDER)
    project_root = _directory(root, PROJECT_FOLDER)
    slug = artwork_filename_stem(name)

    for n in range(1, 10_001):
        stem = slug if n == 1 else f'{slug}-{n}'
        target = artwork_dir / f'{stem}.txt'
        project = project_root / stem
        if target.exists() or target.is_symlink():
            continue
        try:
            project.mkdir(mode=0o700)
        except FileExistsError:
            continue
        created_artwork = False
        try:
            reference = f'{ARTWORK_FOLDER}/{stem}.txt'
            manifest = {
                'format': PROJECT_FORMAT,
                'version': PROJECT_VERSION,
                'artwork': reference,
                'artwork_sha256': sha256(encoded).hexdigest(),
                'source': 'source' + extension,
                'source_sha256': sha256(image_bytes).hexdigest(),
                'settings': asdict(settings),
            }
            raw_manifest = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode('utf-8')
            if len(raw_manifest) > MAX_MANIFEST_BYTES:
                raise ValueError('Project manifest too large.')
            for filename, content in ((manifest['source'], image_bytes),
                                      ('project.json', raw_manifest)):
                with (project / filename).open('xb') as out:
                    out.write(content)
                    out.flush()
                    os.fsync(out.fileno())
            with target.open('xb') as out:
                created_artwork = True
                out.write(encoded)
                out.flush()
                os.fsync(out.fileno())
            return reference
        except FileExistsError:
            # Another writer claimed this .txt in the tiny gap after checking.
            shutil.rmtree(project)
            continue
        except BaseException:
            if created_artwork:
                target.unlink(missing_ok=True)
            shutil.rmtree(project)
            raise
    raise FileExistsError('Too many artworks with that name.')


def load_photo_project(config_dir: Path, reference: str) -> SavedPhotoProject:
    """Read and validate a stored project and its unmodified source image."""
    root = _root(config_dir)
    project = _project_location(root, reference)
    if (root / PROJECT_FOLDER).is_symlink():
        raise ValueError('Project library cannot be a symlink.')
    if project.is_symlink() or not project.is_dir() or project.resolve(strict=True).parent != root / PROJECT_FOLDER:
        raise ValueError('Artwork does not have a saved photo project.')
    manifest_path = project / 'project.json'
    if manifest_path.is_symlink() or not manifest_path.is_file() or manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError('Project metadata is missing or oversized.')
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('Invalid project metadata.') from error
    if (not isinstance(manifest, dict) or set(manifest) != {
            'format', 'version', 'artwork', 'artwork_sha256', 'source',
            'source_sha256', 'settings'} or manifest['format'] != PROJECT_FORMAT
            or type(manifest['version']) is not int or manifest['version'] != PROJECT_VERSION
            or manifest['artwork'] != reference):
        raise ValueError('Unsupported or mismatched project metadata.')
    source_name = manifest['source']
    if not isinstance(source_name, str) or source_name not in {'source' + x for x in SOURCE_EXTENSIONS}:
        raise ValueError('Invalid embedded photo name.')
    source = project / source_name
    if source.is_symlink() or not source.is_file() or not 0 < source.stat().st_size <= MAX_SOURCE_BYTES:
        raise ValueError('Embedded source photo is missing or oversized.')
    if sha256(source.read_bytes()).hexdigest() != manifest['source_sha256']:
        raise ValueError('Embedded photo has been modified or damaged.')
    if any(not isinstance(manifest[key], str) or len(manifest[key]) != 64 or
           any(c not in '0123456789abcdef' for c in manifest[key])
           for key in ('source_sha256', 'artwork_sha256')):
        raise ValueError('Invalid project checksum.')
    opts = _validated_settings(manifest['settings'])
    art_path = root / reference
    if art_path.is_symlink() or not art_path.is_file() or art_path.stat().st_size > MAX_TEXT_BYTES:
        raise ValueError('Project artwork is missing or oversized.')
    modified = sha256(art_path.read_bytes()).hexdigest() != manifest['artwork_sha256']
    return SavedPhotoProject(reference, source, opts, modified)
