"""Local ASCII artwork catalogue and safe optional tag metadata (GTK-free).

The catalogue never edits a renderer asset.  It scans the managed artworks/
folder only, does not follow symlinks, keeps bounded in-memory previews, and
reads/writes optional tags in a separate private metadata folder.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit
import json
import os
from pathlib import Path
import tempfile
import unicodedata

from artwork_library import ARTWORK_FOLDER, valid_artwork_reference
from photo_project import reference_for_artwork

META_FOLDER = 'artwork-meta'
MAX_ASSET_BYTES = 2_000_000
MAX_META_BYTES = 8192
MAX_TAGS = 12
MAX_TAG_LENGTH = 24
PREVIEW_LINES = 32
PREVIEW_COLUMNS = 112


@dataclass(frozen=True)
class LocalArtwork:
    reference: str
    title: str
    preview: str
    columns: int
    rows: int
    orientation: str
    kind: str
    tags: tuple[str, ...]
    author: str = ""
    description: str = ""
    license: str = ""
    source_url: str = ""


@dataclass(frozen=True)
class ArtworkMetadata:
    tags: tuple[str, ...] = ()
    author: str = ""
    description: str = ""
    license: str = ""
    source_url: str = ""


def _managed_root(config_dir: Path) -> Path:
    return Path(config_dir).expanduser().resolve(strict=True)


def _managed_folder(root: Path, name: str) -> Path:
    folder = root / name
    if folder.is_symlink():
        raise ValueError(f'{name} must not be a symbolic link.')
    if folder.exists() and (not folder.is_dir() or folder.resolve(strict=True).parent != root):
        raise ValueError(f'Invalid {name} directory.')
    return folder


def _art_path(root: Path, reference: str) -> Path:
    if not valid_artwork_reference(reference) or not reference.startswith(ARTWORK_FOLDER + '/'):
        raise ValueError('Not a managed artwork.')
    _managed_folder(root, ARTWORK_FOLDER)
    path = root / reference
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True).parent != root / ARTWORK_FOLDER:
        raise ValueError('Not a regular managed artwork.')
    return path


def _validate_tags(tags) -> tuple[str, ...]:
    if not isinstance(tags, (tuple, list)) or len(tags) > MAX_TAGS:
        raise ValueError('Expected up to 12 tags.')
    result = []
    seen = set()
    for raw in tags:
        if not isinstance(raw, str):
            raise ValueError('Tags must be text.')
        tag = unicodedata.normalize('NFC', raw.strip())
        if (not tag or len(tag) > MAX_TAG_LENGTH or any(ord(ch) < 32 or ord(ch) == 127 for ch in tag)
                or ',' in tag):
            raise ValueError('Each tag must be 1–24 characters without commas or controls.')
        key = tag.casefold()
        if key in seen:
            raise ValueError('Duplicate tag.')
        seen.add(key)
        result.append(tag)
    return tuple(result)


def _meta_file(root: Path, reference: str) -> Path:
    stem = Path(reference).stem
    return _managed_folder(root, META_FOLDER) / (stem + '.json')


def _valid_field(value: str, field: str, limit: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f'{field} must be text.')
    value = unicodedata.normalize('NFC', value.strip())
    if len(value) > limit or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError(f'{field} contains invalid characters or is too long.')
    return value


def _validate_metadata(meta: ArtworkMetadata) -> ArtworkMetadata:
    if not isinstance(meta, ArtworkMetadata):
        raise ValueError('Expected artwork metadata.')
    url = _valid_field(meta.source_url, 'Source URL', 400)
    if url:
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or
                parsed.password or parsed.port not in (None, 443) or '\\' in url):
            raise ValueError('Source URL must be a normal HTTPS link.')
    return ArtworkMetadata(
        _validate_tags(meta.tags),
        _valid_field(meta.author, 'Author', 100),
        _valid_field(meta.description, 'Description', 600),
        _valid_field(meta.license, 'License', 120), url,
    )


def load_metadata(config_dir: Path, reference: str) -> ArtworkMetadata:
    root = _managed_root(config_dir)
    _art_path(root, reference)
    location = _meta_file(root, reference)
    if location.is_symlink():
        raise ValueError('Artwork metadata cannot be a symlink.')
    if not location.exists():
        return ArtworkMetadata()
    if not location.is_file() or location.stat().st_size > MAX_META_BYTES:
        raise ValueError('Artwork metadata is invalid or oversized.')
    try:
        obj = json.loads(location.read_text(encoding='utf-8'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Corrupt artwork metadata.') from exc
    if not isinstance(obj, dict) or obj.get('artwork') != reference or type(obj.get('version')) is not int:
        raise ValueError('Unsupported artwork metadata.')
    if obj['version'] == 1 and set(obj) == {'version', 'artwork', 'tags'}:
        if not isinstance(obj['tags'], list):
            raise ValueError('Invalid artwork tags.')
        return _validate_metadata(ArtworkMetadata(tuple(obj['tags'])))
    if obj['version'] == 2 and set(obj) == {'version', 'artwork', 'tags', 'author', 'description', 'license', 'source_url'}:
        if not isinstance(obj['tags'], list):
            raise ValueError('Invalid artwork tags.')
        return _validate_metadata(ArtworkMetadata(tuple(obj['tags']), obj['author'],
                obj['description'], obj['license'], obj['source_url']))
    raise ValueError('Unsupported artwork metadata version.')


def save_metadata(config_dir: Path, reference: str, metadata: ArtworkMetadata) -> ArtworkMetadata:
    """Atomically write sidecar metadata, never the ASCII asset itself."""
    root = _managed_root(config_dir)
    _art_path(root, reference)
    meta = _validate_metadata(metadata)
    directory = _managed_folder(root, META_FOLDER)
    directory.mkdir(mode=0o700, exist_ok=True)
    target = _meta_file(root, reference)
    if target.is_symlink():
        raise ValueError('Artwork metadata cannot be a symlink.')
    encoded = (json.dumps({'version': 2, 'artwork': reference, 'tags': list(meta.tags),
                           'author': meta.author, 'description': meta.description,
                           'license': meta.license, 'source_url': meta.source_url},
                          ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
    if len(encoded) > MAX_META_BYTES:
        raise ValueError('Artwork metadata is too large.')
    fd, temp_name = tempfile.mkstemp(prefix='.metadata-', dir=directory)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(encoded)
            output.flush()
            os.fsync(output.fileno())
        if target.is_symlink():
            raise ValueError('Artwork metadata cannot be a symlink.')
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    return meta


def load_tags(config_dir: Path, reference: str) -> tuple[str, ...]:
    """Legacy V90 public API; supports upgraded V92 metadata."""
    return load_metadata(config_dir, reference).tags


def save_tags(config_dir: Path, reference: str, tags) -> tuple[str, ...]:
    """Keep existing attribution fields when the tags alone are edited."""
    old = load_metadata(config_dir, reference)
    updated = ArtworkMetadata(_validate_tags(tags), old.author, old.description,
                              old.license, old.source_url)
    return save_metadata(config_dir, reference, updated).tags


def _safe_preview(text: str) -> str:
    lines = text.splitlines()[:PREVIEW_LINES]
    clean = []
    for line in lines:
        line = line.expandtabs(4)
        clean.append(''.join(ch for ch in line[:PREVIEW_COLUMNS] if ch.isprintable()))
    if len(text.splitlines()) > PREVIEW_LINES:
        clean.append('…')
    return '\n'.join(clean)


def _orient(cols: int, rows: int) -> str:
    # Typical terminal glyph cells are approximately half as wide as tall.
    aspect = cols / max(1, rows * 2)
    return 'Landscape' if aspect > 1.3 else 'Portrait' if aspect < .75 else 'Square'


def list_artworks(config_dir: Path) -> tuple[list[LocalArtwork], int]:
    """Return sorted entries and number of invalid/unreadable files skipped."""
    root = _managed_root(config_dir)
    folder = _managed_folder(root, ARTWORK_FOLDER)
    if not folder.exists():
        return [], 0
    results = []
    skipped = 0
    for path in sorted(folder.iterdir(), key=lambda item: item.name.casefold()):
        reference = f'{ARTWORK_FOLDER}/{path.name}'
        if not valid_artwork_reference(reference):
            continue
        try:
            actual = _art_path(root, reference)
            if actual.stat().st_size > MAX_ASSET_BYTES:
                raise ValueError('Oversized artwork')
            content = actual.read_text(encoding='utf-8')
            lines = content.splitlines()
            cols = max((len(line.expandtabs(4)) for line in lines), default=0)
            try:
                metadata = load_metadata(root, reference)
            except (OSError, ValueError, UnicodeError):
                # A corrupt optional tag file must not hide a valid artwork.
                metadata = ArtworkMetadata()
                skipped += 1
            kind = 'Photo project' if reference_for_artwork(root, actual) else 'Text artwork'
            results.append(LocalArtwork(reference, actual.stem.replace('-', ' ').strip().title(),
                                        _safe_preview(content), cols, len(lines),
                                        _orient(cols, len(lines)), kind, metadata.tags,
                                        metadata.author, metadata.description,
                                        metadata.license, metadata.source_url))
        except (OSError, ValueError, UnicodeError):
            skipped += 1
    return results, skipped


def filter_artworks(artworks: list[LocalArtwork], query: str = '',
                    kind: str = 'All', orientation: str = 'All') -> list[LocalArtwork]:
    terms = query.casefold().split()
    return [art for art in artworks if
            (kind == 'All' or art.kind == kind) and
            (orientation == 'All' or art.orientation == orientation) and
            all(term in f'{art.title} {art.reference} {" ".join(art.tags)} {art.author} {art.description} {art.license}'.casefold() for term in terms)]
