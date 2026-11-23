"""Small, seekable previews; no runtime image decoder and no GTK requirement.

Each .aspr file is a ZIP containing metadata.json and downsampled, deflated
RGBA frames. V72 packs also contain one-byte coverage masks so the preview
can use the user's palette without a runtime image-processing dependency.
Frames are only decompressed on demand and are never cached here.
"""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from preview_tint import coverage_mask


class PackedPreview:
    def __init__(self, path: Path):
        self._zip = ZipFile(path)
        try:
            info = json.loads(self._zip.read('metadata.json'))
            self.width, self.height = int(info['width']), int(info['height'])
            self.delays = tuple(int(ms) for ms in info['delays_ms'])
            if not (0 < self.width <= 256 and 0 < self.height <= 100 and 1 <= len(self.delays) <= 40):
                raise ValueError('preview dimensions or frame count out of bounds')
            if not all(70 <= d <= 1000 for d in self.delays):
                raise ValueError('invalid preview frame delays')
            self.frame_count = len(self.delays)
        except Exception:
            self._zip.close()
            raise

    def frame(self, index: int) -> bytes:
        if not 0 <= index < self.frame_count:
            raise IndexError(index)
        data = self._zip.read(f'frames/{index:03d}.rgba')
        if len(data) != self.width * self.height * 4:
            raise ValueError('corrupt preview pixel data')
        return data

    def mask_frame(self, index: int) -> bytes:
        """Read a compact tint mask; support pre-V72 assets as a fallback."""
        if not 0 <= index < self.frame_count:
            raise IndexError(index)
        try:
            pixels = self._zip.read(f'masks/{index:03d}.gray')
        except KeyError:
            pixels = coverage_mask(self.frame(index))
        if len(pixels) != self.width * self.height:
            raise ValueError('corrupt preview coverage mask')
        return pixels

    def close(self) -> None:
        self._zip.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
