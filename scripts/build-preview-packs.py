#!/usr/bin/env python3
"""Offline preprocessing of upstream GIFs; Pillow is NOT needed at runtime.

Generate compact, bounded 224px-wide frames, reducing 16.7fps originals to
8.3fps previews. GTK consumes raw frames directly without Glycin.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preview_tint import coverage_mask


def pack_preview(source: Path, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as animation:
        width = 224
        height = max(1, round(animation.height * width / animation.width))
        # Every second GIF frame; keep enough motion to identify the effect.
        frame_numbers = list(range(0, animation.n_frames, 2))[:30]
        delays = []
        with ZipFile(target, 'w', compression=ZIP_DEFLATED, compresslevel=7) as output:
            for slot, index in enumerate(frame_numbers):
                animation.seek(index)
                pixels = animation.convert('RGBA').resize((width, height), Image.Resampling.LANCZOS)
                rgba = pixels.tobytes()
                output.writestr(f'frames/{slot:03d}.rgba', rgba)
                output.writestr(f'masks/{slot:03d}.gray', coverage_mask(rgba))
                delay_ms = 0
                for part in range(index, min(index + 2, animation.n_frames)):
                    animation.seek(part)
                    delay_ms += max(30, int(animation.info.get('duration') or 60))
                delays.append(min(1000, max(70, delay_ms)))
            output.writestr('metadata.json', json.dumps({
                'width': width, 'height': height, 'delays_ms': delays,
                'source': source.name, 'format_version': 2, 'mask_version': 1,
            }))
    return len(delays)


def main():
    root = Path(__file__).resolve().parent.parent
    source = root / 'ttfx-rust/docs/effects'
    target = root / 'preview-packs'
    counts = {p.stem: pack_preview(p, target / f'{p.stem}.aspr') for p in sorted(source.glob('*.gif'))}
    if len(counts) != 37:
        raise SystemExit(f'Expected 37 effect previews, got {len(counts)}')
    total = sum(p.stat().st_size for p in target.glob('*.aspr'))
    print(f'Built {len(counts)} packed previews ({total / 1024 / 1024:.1f} MiB compressed); '
          f'{sum(counts.values())} frames at <=224px')


if __name__ == '__main__':
    main()
