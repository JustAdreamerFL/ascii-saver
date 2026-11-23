"""V94: user-defined monochrome ramps are renderer-safe and reversible."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from photo_ascii import (AVAILABLE_RAMPS, CUSTOM_RAMP_NAME, DEFAULT_CUSTOM_RAMP,
                         RAMPS, PhotoSettings, photo_to_ascii)
from photo_project import load_photo_project, save_photo_project
from photo_presets import list_presets, save_preset

ROOT = Path(__file__).resolve().parents[1]


def uniform(value: int, w: int = 32, h: int = 32) -> bytes:
    return bytes([value] * (w * h * 3))


class CustomRampTests(unittest.TestCase):
    def setUp(self):
        self.options = PhotoSettings(columns=16, rows=8, ramp=CUSTOM_RAMP_NAME,
                                     custom_ramp='Xo.')

    def test_select_custom_density_sequence_and_append_blank(self):
        # Both density endpoints are intentional and independent of any
        # built-in ramp. The lightest tone always maps to whitespace.
        output_dark = photo_to_ascii(uniform(0), 32, 32, settings=self.options)
        output_light = photo_to_ascii(uniform(255), 32, 32, settings=self.options)
        self.assertEqual(output_dark, ('X' * 16 + '\n') * 8)
        self.assertEqual(output_light, (' ' * 16 + '\n') * 8)
        gray = photo_to_ascii(uniform(80), 32, 32, settings=self.options)
        self.assertEqual(gray, ('o' * 16 + '\n') * 8)
        self.assertEqual(AVAILABLE_RAMPS[-1], 'Custom')
        self.assertNotIn('Custom', RAMPS)

    def test_explicit_custom_ramp_overrides_default_without_changing_standard(self):
        img = uniform(115)
        original = photo_to_ascii(img, 32, 32, settings=PhotoSettings(columns=16, rows=8))
        altered = photo_to_ascii(img, 32, 32, settings=PhotoSettings(columns=16, rows=8,
                                  custom_ramp='ABC'))
        self.assertEqual(original, altered)
        custom = photo_to_ascii(img, 32, 32, settings=self.options)
        self.assertNotEqual(custom, original)
        self.assertTrue(set(custom.replace('\n', '')) <= set('Xo. '))

    def test_unique_ascii_validation_prevents_control_code_or_unicode_injection(self):
        invalid = ('', '.', ' ', 'A ', 'AA', 'ABBA', 'A\nB', 'A\x1bB',
                   'é@', 'A\u202eB', 'A\tB', 'A' * 64,
                   'a' * 2, 123, None)
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(self.options, custom_ramp=value).validate()
        for value in ('@#', 'A$*.;', '0123456789', DEFAULT_CUSTOM_RAMP):
            with self.subTest(value=value):
                replace(self.options, custom_ramp=value).validate()

    def test_project_reopens_exact_user_ramp_and_prior_manifests_still_load(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            source = b'BM' + bytes(150)
            ref = save_photo_project(root, 'my-ramp', 'XXX\n', source, '.bmp', self.options)
            result = load_photo_project(root, ref)
            self.assertEqual(result.settings, self.options)
            manifest = root / 'photo-projects/my-ramp/project.json'
            data = json.loads(manifest.read_text())
            data['settings'].pop('custom_ramp')
            manifest.write_text(json.dumps(data))
            old = load_photo_project(root, ref)
            self.assertEqual(old.settings.custom_ramp, DEFAULT_CUSTOM_RAMP)
            self.assertEqual(old.settings.ramp, CUSTOM_RAMP_NAME)
            # Missing custom fields are valid only for legacy records whose
            # names still declare a valid custom-ramp selection.
            data['settings']['custom_ramp'] = 'OO'
            manifest.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_photo_project(root, ref)

    def test_preset_roundtrip_and_legacy_recipe_compatibility(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            own = save_preset(root, 'Dots', self.options)
            self.assertEqual(next(p.settings for p in list_presets(root)[0]
                                  if p.key == own.key), self.options)
            path = root / 'photo-presets/dots.json'
            data = json.loads(path.read_text())
            data['settings'].pop('custom_ramp')
            path.write_text(json.dumps(data))
            old = next(p.settings for p in list_presets(root)[0] if p.key == own.key)
            self.assertEqual(old.custom_ramp, DEFAULT_CUSTOM_RAMP)


class CustomRampUIContract(unittest.TestCase):
    def test_live_render_and_no_stale_export_after_invalid_user_typing(self):
        source = (SRC / 'photo_ascii_view.py').read_text()
        ast.parse(source)
        for expected in ("self.ramp.set_model(Gtk.StringList.new(list(AVAILABLE_RAMPS)))",
                         "self.custom_ramp = Adw.EntryRow(",
                         "self.custom_ramp.set_sensitive(is_custom)",
                         "self.advanced.set_expanded(True)",
                         "(self.custom_ramp, 'notify::text')",
                         "custom_ramp=custom",
                         "self.preview.get_buffer().set_text('')",
                         "self.use_button.set_sensitive(False)",
                         "self.save_new_button.set_sensitive(False)"):
            self.assertIn(expected, source)

    def test_package_version_and_historical_docs(self):
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertGreaterEqual(int(version.split('.')[1]), 94)
        self.assertIn(f'BUILD_VERSION = "{version}"', (SRC / 'build_info.py').read_text())
        self.assertIn('photo_ascii photo_ascii_view photo_project photo_presets',
                      (ROOT / 'install.sh').read_text())
        for path in ('ROADMAP.md', 'TASKS.md', 'CHANGELOG.md', 'MASTER-BACKLOG.md', 'RELEASE-V94.md'):
            self.assertIn('V94', read_source(path))


if __name__ == '__main__':
    unittest.main()
