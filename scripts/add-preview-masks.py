#!/usr/bin/env python3
"""Add recolorable masks to existing .aspr previews, without Pillow.

Run once for releases made from pre-V72 preview packs. Original RGBA frames
remain intact, so older installations can still decode the assets.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from preview_tint import coverage_mask


def add_masks(path: Path) -> int:
    with ZipFile(path) as original:
        metadata = json.loads(original.read('metadata.json'))
        if metadata.get('mask_version') == 1:
            return 0
        frames = len(metadata['delays_ms'])
        with NamedTemporaryFile(prefix=path.stem + '-', suffix='.aspr',
                                dir=path.parent, delete=False) as temporary:
            target = Path(temporary.name)
        try:
            with ZipFile(target, 'w', compression=ZIP_DEFLATED, compresslevel=7) as output:
                for entry in original.infolist():
                    if entry.filename != 'metadata.json' and not entry.filename.startswith('masks/'):
                        output.writestr(entry.filename, original.read(entry.filename))
                for index in range(frames):
                    output.writestr(f'masks/{index:03d}.gray',
                                    coverage_mask(original.read(f'frames/{index:03d}.rgba')))
                metadata.update(format_version=2, mask_version=1)
                output.writestr('metadata.json', json.dumps(metadata))
            target.replace(path)
        finally:
            target.unlink(missing_ok=True)
    return frames


def main():
    count = 0
    total = 0
    for path in sorted((ROOT / 'preview-packs').glob('*.aspr')):
        total += add_masks(path)
        count += 1
    print(f'Processed {count} preview packs; added {total} compact tint masks')


if __name__ == '__main__':
    main()
