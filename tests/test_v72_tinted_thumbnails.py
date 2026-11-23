"""V72: selected palette recolors all 37 compact sample animations."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from preview_asset import PackedPreview
from preview_tint import SOURCE_BACKGROUND, coverage_mask, tint_mask
from effect_selection import EFFECTS

ROOT = Path(__file__).resolve().parents[1]


class TintMathTests(unittest.TestCase):
    def test_background_noise_is_ignored_and_hues_become_coverage(self):
        background = bytes((*SOURCE_BACKGROUND, 255))
        near_background = bytes((21, 18, 28, 255))
        red = bytes((255, 0, 0, 255))
        green = bytes((0, 255, 0, 255))
        blue = bytes((0, 0, 255, 255))
        mask = coverage_mask(background + near_background + red + green + blue)
        self.assertEqual(mask[:2], b'\0\0')
        self.assertEqual(mask[2:4], b'\xff\xff')
        self.assertGreaterEqual(mask[4], 240)

    def test_transparency_and_invalid_rgba(self):
        self.assertEqual(coverage_mask(bytes((255, 0, 0, 0))), b'\0')
        self.assertEqual(coverage_mask(bytes((255, 0, 0, 128))), bytes((128,)))
        with self.assertRaises(ValueError):
            coverage_mask(b'bad')

    def test_foreground_background_exact_and_semigray(self):
        rendered = tint_mask(bytes((0, 127, 255)), '#FF0000', '#0000FF')
        self.assertEqual(rendered[:4], bytes((0, 0, 255, 255)))
        self.assertEqual(rendered[8:], bytes((255, 0, 0, 255)))
        mid = rendered[4:8]
        self.assertGreaterEqual(mid[0], 126)
        self.assertLessEqual(mid[2], 129)
        self.assertEqual(mid[1], 0)
        self.assertEqual(mid[3], 255)
        self.assertEqual(tint_mask(b'\0\xff', '#aBcDef', '#123456'),
                         bytes((0x12, 0x34, 0x56, 255, 0xAB, 0xCD, 0xEF, 255)))

    def test_tint_rejects_invalid_color(self):
        with self.assertRaises(ValueError):
            tint_mask(b'\xff', 'red', '#000000')
        with self.assertRaises(ValueError):
            tint_mask(b'\xff', '#ABCDEF', '#XX0000')


class PackedAssetTests(unittest.TestCase):
    def test_every_pack_has_precomputed_masks_for_every_frame(self):
        self.assertEqual(len(EFFECTS), 37)
        for name in EFFECTS:
            with self.subTest(name=name):
                path = ROOT / 'preview-packs' / f'{name}.aspr'
                with ZipFile(path) as archive:
                    metadata = json.loads(archive.read('metadata.json'))
                    self.assertEqual(metadata['mask_version'], 1)
                    self.assertEqual(metadata['format_version'], 2)
                    self.assertEqual(len([f for f in archive.namelist()
                                          if f.startswith('masks/')]), len(metadata['delays_ms']))
                with PackedPreview(path) as preview:
                    self.assertEqual(len(preview.mask_frame(0)), preview.width * preview.height)
                    self.assertEqual(len(preview.mask_frame(preview.frame_count - 1)),
                                     preview.width * preview.height)
                    self.assertEqual(len(tint_mask(preview.mask_frame(0), '#0DAA77', '#080808')),
                                     preview.width * preview.height * 4)
                    with self.assertRaises(IndexError):
                        preview.mask_frame(preview.frame_count)

    def test_legacy_pack_falls_back_to_original_rgba(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'legacy.aspr'
            with ZipFile(target, 'w', compression=ZIP_DEFLATED) as archive:
                archive.writestr('metadata.json', json.dumps({
                    'width': 1, 'height': 1, 'delays_ms': [100]}))
                archive.writestr('frames/000.rgba', bytes((255, 0, 0, 255)))
            with PackedPreview(target) as pack:
                self.assertEqual(pack.mask_frame(0), b'\xff')

    def test_invalid_or_truncated_mask_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'broken.aspr'
            with ZipFile(target, 'w') as archive:
                archive.writestr('metadata.json', json.dumps({
                    'width': 2, 'height': 1, 'delays_ms': [100]}))
                archive.writestr('masks/000.gray', b'\x01')
            with PackedPreview(target) as pack:
                with self.assertRaises(ValueError):
                    pack.mask_frame(0)


class IntegrationContractTests(unittest.TestCase):
    def test_gallery_uses_saved_palette_initially_and_unsaved_changes(self):
        source = (ROOT / 'preferences_gallery_view.py').read_text()
        state = (ROOT / 'preferences_state.py').read_text()
        animated = (ROOT / 'animated_preview.py').read_text()
        self.assertIn('palette_color_for_round(palette_config, None, 0)', source)
        self.assertIn('foreground=thumbnail_color', source)
        self.assertIn('background=thumbnail_background', source)
        self.assertIn('button.connect("notify::rgba", self._refresh_gallery_palette)', state)
        self.assertIn('self.background.connect("notify::rgba", self._refresh_gallery_palette)', state)
        self.assertIn('self._refresh_gallery_palette()\n        if hasattr(self, "_saved_snapshot"):', state)
        self.assertIn('preview.set_colors(color, background)', state)
        self.assertIn('pack.mask_frame(index)', animated)
        self.assertIn('self._set_frame_texture(pack, index)', animated)
        self.assertIn('self._active and self._pack is not None', animated)
        # No per-frame process spawn or GIF decoder is introduced.
        self.assertNotIn('subprocess', animated)
        self.assertNotIn('from gi.repository import GdkPixbuf', animated)

    def test_playlist_samples_use_same_saved_colors(self):
        source = (ROOT / 'playlist_editor.py').read_text()
        self.assertIn('palette_color_for_round(raw, None, 0)', source)
        self.assertIn('foreground=self.thumbnail_foreground', source)
        self.assertIn('background=self.thumbnail_background', source)

    def test_installer_includes_tint_module(self):
        installer = (ROOT / 'install.sh').read_text()
        self.assertIn('"$source_dir/preview_tint.py"', installer)


if __name__ == '__main__':
    unittest.main()
