#!/usr/bin/env python3
"""Offline checks for installer, preview packs and renderer payload."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
from effect_selection import EFFECTS
from preview_asset import PackedPreview

assert len(EFFECTS) == len(set(EFFECTS)) == 37, "Effect catalog should contain 37 names"
preview_dir = root / "preview-packs"
missing = [name for name in EFFECTS if not (preview_dir / f"{name}.aspr").is_file()]
assert not missing, f"Missing packed previews: {missing}"
for name in EFFECTS:
    path = preview_dir / f"{name}.aspr"
    assert path.stat().st_size < 750_000, f"Preview pack unexpectedly large: {name}"
    with PackedPreview(path) as pack:
        assert pack.width <= 256 and pack.height <= 100
        assert 2 <= pack.frame_count <= 40
        first = pack.frame(0)
        middle = pack.frame(pack.frame_count // 2)
        assert first != middle, f"Preview does not change frames: {name}"
        assert len(pack.mask_frame(0)) == pack.width * pack.height, f"Missing tint mask: {name}"
        assert len(pack.mask_frame(pack.frame_count - 1)) == pack.width * pack.height
installer = (root / "install.sh").read_text()
for marker in ("preview-packs/*.aspr", '"$staged_app/effects"',
               '"$py_src/preview_asset.py"', '"$py_src/preview_tint.py"',
               '"$py_src/effect_library.py"'):
    assert marker in installer, f"Installer missing asset staging instruction: {marker}"
assert 'ctl.data_dir / "effects"' in (root / "src" / "preferences_gallery_view.py").read_text()
assert (root / "ttfx-rust/Cargo.lock").is_file()
print(f"PASS: {len(EFFECTS)} effect IDs, small decoder-free preview packs and installer payload")
