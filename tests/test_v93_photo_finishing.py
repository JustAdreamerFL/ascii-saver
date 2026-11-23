"""V93 photo finishing: deterministic conversion, legacy recipe compatibility and UI."""
from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from photo_ascii import PhotoSettings, photo_to_ascii
from photo_project import load_photo_project, save_photo_project
from photo_presets import list_presets, save_preset

ROOT = Path(__file__).resolve().parents[1]


def rgb_gradient(w=48, h=32):
    return bytes(channel for y in range(h) for x in range(w)
                 for channel in (round(x * 255 / (w - 1)),) * 3)


class PhotoFinishingTests(unittest.TestCase):
    def setUp(self):
        self.defaults = PhotoSettings(columns=32, rows=16)

    def test_default_options_keep_original_output(self):
        image = rgb_gradient()
        reference = photo_to_ascii(image, 48, 32, settings=self.defaults)
        explicit = replace(self.defaults, posterize=0, alpha_background='white')
        self.assertEqual(photo_to_ascii(image, 48, 32, settings=explicit), reference)

    def test_posterization_restricts_tones_to_selected_bands(self):
        image = rgb_gradient()
        original = photo_to_ascii(image, 48, 32, settings=self.defaults)
        poster = photo_to_ascii(image, 48, 32,
                                settings=replace(self.defaults, posterize=3))
        self.assertGreater(len(set(original.replace('\n', ''))), 3)
        self.assertEqual(len(set(poster.replace('\n', ''))), 3)
        self.assertNotEqual(original, poster)
        self.assertEqual(poster, photo_to_ascii(image, 48, 32,
                         settings=replace(self.defaults, posterize=3)))

    def test_full_transparency_respects_matte_and_default_is_white(self):
        # Every pixel is transparent red. Only the chosen background should
        # determine the resulting density; hidden RGB must not bleed through.
        rgba = bytes([255, 0, 0, 0]) * (32 * 32)
        outputs = [photo_to_ascii(rgba, 32, 32, channels=4,
                   settings=replace(self.defaults, alpha_background=bg))
                   for bg in ('white', 'gray', 'black')]
        self.assertEqual(set(outputs[0].replace('\n', '')), {' '})
        self.assertEqual(set(outputs[2].replace('\n', '')), {'@'})
        self.assertNotEqual(outputs[0], outputs[1])
        self.assertNotEqual(outputs[1], outputs[2])

    def test_transparent_matte_does_not_affect_opaque_rgb_or_rgba(self):
        rgb = bytes([60, 190, 95]) * (32 * 32)
        rgba = bytes([60, 190, 95, 255]) * (32 * 32)
        for bg in ('white', 'gray', 'black'):
            with self.subTest(bg=bg):
                self.assertEqual(photo_to_ascii(rgb, 32, 32, settings=self.defaults),
                                 photo_to_ascii(rgb, 32, 32,
                                     settings=replace(self.defaults, alpha_background=bg)))
                self.assertEqual(photo_to_ascii(rgb, 32, 32, settings=self.defaults),
                                 photo_to_ascii(rgba, 32, 32, channels=4,
                                     settings=replace(self.defaults, alpha_background=bg)))

    def test_center_fit_padding_stays_blank_even_with_black_matte(self):
        rgba = bytes([0, 0, 0, 0]) * (64 * 8)
        opts = replace(self.defaults, fit='fit', alpha_background='black', posterize=2, dither=True)
        rows = photo_to_ascii(rgba, 64, 8, channels=4, settings=opts).splitlines()
        self.assertEqual(rows[0], ' ' * opts.columns)
        self.assertEqual(rows[-1], ' ' * opts.columns)
        self.assertTrue(any('@' in line for line in rows))

    def test_invalid_posterization_and_matte_rejected(self):
        for kwargs in ({'posterize': -1}, {'posterize': 1}, {'posterize': 9},
                       {'posterize': True}, {'posterize': 3.5},
                       {'alpha_background': 'transparent'},
                       {'alpha_background': 7}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(self.defaults, **kwargs).validate()

    def test_modern_photo_project_roundtrip(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            settings = replace(self.defaults, posterize=4, alpha_background='gray', dither=True)
            ref = save_photo_project(root, 'graphic', '#\n', b'BM' + bytes(200), '.bmp', settings)
            self.assertEqual(load_photo_project(root, ref).settings, settings)

    def test_legacy_v89_photo_project_missing_new_keys_still_loads(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            ref = save_photo_project(root, 'older', '@\n', b'BM' + bytes(200), '.bmp', self.defaults)
            manifest = root / 'photo-projects/older/project.json'
            payload = json.loads(manifest.read_text())
            payload['settings'].pop('posterize')
            payload['settings'].pop('alpha_background')
            manifest.write_text(json.dumps(payload), encoding='utf-8')
            self.assertEqual(load_photo_project(root, ref).settings, self.defaults)
            payload['settings']['made_up_feature'] = 22
            manifest.write_text(json.dumps(payload), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_photo_project(root, ref)
            payload['settings'].pop('made_up_feature')
            payload['settings'].pop('contrast')
            manifest.write_text(json.dumps(payload), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_photo_project(root, ref)

    def test_legacy_v91_personal_preset_missing_new_keys_still_loads(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            preset = save_preset(root, 'Old grain', self.defaults)
            file = root / 'photo-presets/old-grain.json'
            payload = json.loads(file.read_text())
            payload['settings'].pop('posterize')
            payload['settings'].pop('alpha_background')
            file.write_text(json.dumps(payload), encoding='utf-8')
            loaded, skipped = list_presets(root)
            self.assertEqual(skipped, 0)
            self.assertEqual(loaded[-1].key, preset.key)
            self.assertEqual(loaded[-1].settings, self.defaults)
            updated = replace(self.defaults, posterize=5, alpha_background='black')
            new = save_preset(root, 'New grain', updated)
            self.assertEqual(next(p.settings for p in list_presets(root)[0] if p.key == new.key), updated)
            self.assertEqual(new.settings, updated)


class FinishingUIContracts(unittest.TestCase):
    def test_advanced_controls_save_reopen_presets_and_live_preview(self):
        view = (ROOT / 'photo_ascii_view.py').read_text()
        ast.parse(view)
        for part in ("self.advanced.set_expanded(False)",
                     "self.posterize = Adw.ComboRow(",
                     "self.alpha_background = Adw.ComboRow(",
                     "self.alpha_background.set_sensitive(pixbuf.get_has_alpha())",
                     "(self.posterize, 'notify::selected')",
                     "(self.alpha_background, 'notify::selected')",
                     "self.posterize.set_selected(0 if settings.posterize == 0 else settings.posterize - 1)",
                     "self.alpha_background.set_selected(('white', 'gray', 'black').index(settings.alpha_background))",
                     "posterize=0 if self.posterize.get_selected() == 0 else self.posterize.get_selected() + 1",
                     "alpha_background=('white', 'gray', 'black')[self.alpha_background.get_selected()]",
                     'self.posterize.set_selected(0)', 'self.alpha_background.set_selected(0)',
                     'self._ensure_latest_preview()',
                     'save_photo_project(self.config_dir, self.art_name.get_text()'):
            self.assertIn(part, view)

    def test_version_documentation_and_installer(self):
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertGreaterEqual(tuple(map(int, version.split('.'))), (0, 93, 0))
        self.assertIn(f'BUILD_VERSION = "{version}"', (ROOT / 'build_info.py').read_text())
        self.assertIn('photo_ascii photo_ascii_view photo_project photo_presets',
                      (ROOT / 'install.sh').read_text())
        for file in ('CHANGELOG.md', 'TASKS.md', 'ROADMAP.md', 'RELEASE-V93.md'):
            self.assertIn('V93', (ROOT / file).read_text(), file)


if __name__ == '__main__':
    unittest.main()
