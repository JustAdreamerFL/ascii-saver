"""Optional read-only ascii-bin online provider, independent of GTK.

One explicitly selected public text feed, no scraping, credentials, execution,
or automatic downloads. Remote art is always treated as untrusted text. A cached
copy is usable offline. Rights to individual collected works are unverified.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
import os
import random
from pathlib import Path
import re
import tempfile
from urllib.request import Request, urlopen

from artwork_catalog import ArtworkMetadata, _managed_root, _managed_folder, save_metadata
from build_info import BUILD_VERSION
from artwork_library import save_generated_artwork

PROVIDER_NAME = 'ascii-bin'
PROVIDER_HOME = 'https://github.com/amwhoi/ascii-bin'
SOURCE_URL = PROVIDER_HOME + '/blob/main/asciiart_db.txt'
FEED_URL = 'https://raw.githubusercontent.com/amwhoi/ascii-bin/main/asciiart_db.txt'
LICENSE_NOTE = 'CC0 claimed by collection; individual rights unverified'
CACHE_FOLDER = 'online-cache'
CACHE_FILE = 'ascii-bin.txt'
MAX_FEED_BYTES = 3_000_000
MAX_ART_BYTES = 64_000
MAX_ENTRIES = 800
MAX_LINES = 280
MAX_COLUMNS = 360
PAGE_SIZE = 48
SORT_OPTIONS = ('Repository order', 'Title A–Z', 'Smallest first', 'Largest first', 'Shuffle')


@dataclass(frozen=True)
class RemoteArtwork:
    number: int
    title: str
    description: str
    tags: tuple[str, ...]
    artwork: str
    preview: str
    columns: int
    rows: int
    orientation: str
    source_url: str = SOURCE_URL
    license: str = LICENSE_NOTE
    author: str = 'Unknown'


def _clean_line(line: str) -> str:
    # Never interpret terminal escape sequences, control codes or tabs from a
    # third-party repository as instructions or VTE formatting.
    line = re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07)', '', line)
    return ''.join(ch for ch in line.expandtabs(4) if ch.isprintable() and
                   ch not in '\u202e\u202d\u202a\u202b\u202c\u2066\u2067\u2068\u2069')


def parse_collection(data: bytes) -> tuple[RemoteArtwork, ...]:
    """Parse the documented ===EOF=== / tags: / description: format."""
    if not isinstance(data, bytes) or len(data) > MAX_FEED_BYTES:
        raise ValueError('Online collection is invalid or too large.')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('Online collection is not UTF-8 text.') from exc
    if '===EOF===' not in text:
        raise ValueError('Online collection does not use the expected format.')
    results = []
    for index, chunk in enumerate(re.split(r'(?m)^===EOF===[ \t]*\r?$', text), 1):
        if len(results) >= MAX_ENTRIES:
            break
        raw_lines = chunk.strip('\n\r').splitlines()
        if not raw_lines:
            continue
        description = ''
        tags: tuple[str, ...] = ()
        # A piece's metadata, when present, is trailing lines only.
        while raw_lines:
            tail = raw_lines[-1].strip()
            if tail.lower().startswith('description:') and not description:
                description = _clean_line(tail.partition(':')[2].strip())[:160]
            elif tail.lower().startswith('tags:') and not tags:
                parts = [_clean_line(tag.strip())[:24] for tag in tail.partition(':')[2].split(',')]
                tags = tuple(dict.fromkeys(tag for tag in parts if tag))[:12]
            else:
                break
            raw_lines.pop()
        while raw_lines and not raw_lines[-1].strip():
            raw_lines.pop()
        if not raw_lines or len(raw_lines) > MAX_LINES:
            continue
        lines = [_clean_line(line).rstrip() for line in raw_lines]
        columns = max((len(line) for line in lines), default=0)
        art_text = '\n'.join(lines).rstrip('\n') + '\n'
        if columns > MAX_COLUMNS or not art_text.strip() or len(art_text.encode('utf-8')) > MAX_ART_BYTES:
            continue
        from artwork_catalog import _orient, _safe_preview
        title = (description.split('.')[0][:64] if description else
                 ' / '.join(tags[:2])[:64] if tags else f'Artwork {index:03d}')
        results.append(RemoteArtwork(index, title, description, tags, art_text,
                         _safe_preview(art_text), columns, len(lines), _orient(columns, len(lines))))
    if not results:
        raise ValueError('Online collection contains no usable ASCII artwork.')
    return tuple(results)


def _download_collection() -> bytes:
    req = Request(FEED_URL, headers={'User-Agent': f'ASCII-Saver/{BUILD_VERSION} (art browser)',
                                      'Accept': 'text/plain'})
    with urlopen(req, timeout=12) as response:
        # Do not accept a redirected feed from an unknown host.
        if response.geturl() != FEED_URL:
            raise ValueError('Online provider redirected to an unexpected address.')
        payload = response.read(MAX_FEED_BYTES + 1)
    if len(payload) > MAX_FEED_BYTES:
        raise ValueError('Online collection exceeded the safe download size.')
    return payload


def _cache_path(root: Path) -> Path:
    return _managed_folder(root, CACHE_FOLDER) / CACHE_FILE


def _write_cache(root: Path, payload: bytes) -> None:
    directory = _managed_folder(root, CACHE_FOLDER)
    directory.mkdir(mode=0o700, exist_ok=True)
    target = _cache_path(root)
    if target.is_symlink():
        raise ValueError('Online cache cannot be a symlink.')
    fd, name = tempfile.mkstemp(prefix='.ascii-bin-', dir=directory)
    tmp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        if target.is_symlink():
            raise ValueError('Online cache cannot be a symlink.')
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)


def _read_cache(root: Path) -> bytes:
    target = _cache_path(root)
    if target.is_symlink() or not target.is_file() or target.stat().st_size > MAX_FEED_BYTES:
        raise ValueError('No safe cached online collection is available.')
    return target.read_bytes()


def load_collection(config_dir: Path, *, downloader=None) -> tuple[tuple[RemoteArtwork, ...], str]:
    """Return (arts, status), using cached art on a failed network request.

    All network I/O is opt-in via the user's Browse Online action; the caller
    runs this in a background worker instead of the GTK event loop.
    """
    root = _managed_root(config_dir)
    try:
        payload = (downloader or _download_collection)()
        entries = parse_collection(payload)
        try:
            _write_cache(root, payload)
            return entries, 'Live collection'
        except (OSError, ValueError):
            return entries, 'Live collection (cache unavailable)'
    except (OSError, ValueError, UnicodeError, TimeoutError) as error:
        try:
            entries = parse_collection(_read_cache(root))
        except (OSError, ValueError, UnicodeError) as cache_error:
            raise ValueError(f'Online source unavailable: {error}. No offline cache available.') from cache_error
        return entries, f'Offline cached collection (refresh failed: {error})'


def filter_collection(artworks: tuple[RemoteArtwork, ...] | list[RemoteArtwork],
                      query: str = '', tag: str = 'All', orientation: str = 'All') -> list[RemoteArtwork]:
    terms = query.casefold().split()
    return [item for item in artworks
            if (tag == 'All' or tag.casefold() in (x.casefold() for x in item.tags))
            and (orientation == 'All' or item.orientation == orientation)
            and all(term in f'{item.title} {item.description} {" ".join(item.tags)} {item.artwork[:600]}'.casefold()
                    for term in terms)]


def top_tags(artworks: tuple[RemoteArtwork, ...], limit: int = 18) -> list[str]:
    counts = Counter(tag for item in artworks for tag in item.tags)
    return [tag for tag, _ in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].casefold()))[:limit]]


def import_remote(config_dir: Path, item: RemoteArtwork) -> str:
    """Explicit copy into user's library, with rights caveat and provenance.

    If metadata cannot be saved, roll back only the new file. Never replace a
    previous artwork, even if the title matches or the user imports twice.
    """
    if not isinstance(item, RemoteArtwork) or item.source_url != SOURCE_URL or item.license != LICENSE_NOTE:
        raise ValueError('Unsupported remote artwork provider.')
    if len(item.artwork.encode('utf-8')) > MAX_ART_BYTES or not item.artwork.strip():
        raise ValueError('Remote artwork exceeds safe size limits.')
    root = _managed_root(config_dir)
    reference = save_generated_artwork(root, item.title, item.artwork)
    try:
        description = item.description or f'Imported from ascii-bin entry {item.number}.'
        save_metadata(root, reference, ArtworkMetadata(item.tags, item.author,
                      description[:600], LICENSE_NOTE, SOURCE_URL))
    except BaseException:
        (root / reference).unlink(missing_ok=True)
        raise
    return reference


def sort_collection(artworks: tuple[RemoteArtwork, ...] | list[RemoteArtwork],
                    order: str = 'Repository order', *, seed: int = 0) -> list[RemoteArtwork]:
    """Sort only already loaded items; never fetch or mutate remote artwork.

    The repository carries no reliable publication timestamp or popularity,
    so the UI offers no fictional newest/trending ranking. Shuffle is stable
    for a given seed, allowing progressive list paging without repetition.
    """
    if order not in SORT_OPTIONS:
        raise ValueError('Unknown artwork sorting mode.')
    items = list(artworks)
    if order == 'Title A–Z':
        items.sort(key=lambda art: (art.title.casefold(), art.number))
    elif order == 'Smallest first':
        items.sort(key=lambda art: (art.columns * art.rows, art.number))
    elif order == 'Largest first':
        items.sort(key=lambda art: (-(art.columns * art.rows), art.number))
    elif order == 'Shuffle':
        random.Random(seed).shuffle(items)
    return items
