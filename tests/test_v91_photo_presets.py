"""V91: genuine reusable looks, safe persistence, and progressive GTK contracts."""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from photo_ascii import PhotoSettings
from photo_presets import (BUILTIN_PRESETS, ConversionPreset, delete_preset,
                           list_presets, save_preset)
from photo_project import save_photo_project, load_photo_project

ROOT = Path(__file__).resolve().parents[1]


class CreativePhotoPresetTests(unittest.TestCase):
    def test_six_distinct_builtin_looks_have_valid_distinct_recipes(self):
        self.assertEqual(len(BUILTIN_PRESETS), 6)
        self.assertEqual(len({p.name.casefold() for p in BUILTIN_PRESETS}), 6)
        self.assertEqual(len({p.settings for p in BUILTIN_PRESETS}), 6)
        self.assertTrue(all(p.builtin and p.description for p in BUILTIN_PRESETS))
        for preset in BUILTIN_PRESETS:
            with self.subTest(look=preset.name):
                preset.settings.validate()
        with TemporaryDirectory() as d:
            presets, skipped = list_presets(Path(d))
            self.assertEqual((presets, skipped), (list(BUILTIN_PRESETS), 0))

    def test_personal_preset_roundtrip_and_application_preserves_photo_recipe(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            settings = PhotoSettings(columns=92, rows=19, fit='fit', brightness=-15,
                                     contrast=140, invert=True, ramp='Fine detail',
                                     gamma=1.6, edge=50, dither=True)
            reference = save_photo_project(root, 'Original', 'art\n', b'BMphoto', '.bmp', settings)
            photo_copy = (root / 'photo-projects/original/source.bmp').read_bytes()
            preset = save_preset(root, 'Night Garden', settings)
            self.assertEqual(preset.key, 'custom/night-garden')
            listed, skipped = list_presets(root)
            self.assertEqual(skipped, 0)
            self.assertEqual(listed[-1], preset)
            self.assertEqual(load_photo_project(root, reference).settings, settings)
            self.assertEqual((root / 'photo-projects/original/source.bmp').read_bytes(), photo_copy)
            self.assertEqual((root / reference).read_text(), 'art\n')
            delete_preset(root, preset.key)
            self.assertEqual(list_presets(root), (list(BUILTIN_PRESETS), 0))
            self.assertTrue((root / reference).exists())

    def test_rejects_duplicate_names_invalid_names_and_invalid_settings(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            original = save_preset(root, 'Soft Neon', PhotoSettings())
            target = root / 'photo-presets/soft-neon.json'
            before = target.read_bytes()
            for name in ('Soft Neon', ' soft neon ', 'Classic Terminal', '', '  ',
                         'Bad\nName', 'x'*61, '\x00', '🌙'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    save_preset(root, name, PhotoSettings())
            with self.assertRaises(ValueError):
                save_preset(root, 'Outside', PhotoSettings(columns=600))
            with self.assertRaises(ValueError):
                save_preset(root, 'Outside', None)
            self.assertEqual(target.read_bytes(), before)
            self.assertEqual(list_presets(root)[0][-1], original)

    def test_removal_requires_confirmed_custom_file_and_rejects_traversal(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            user = save_preset(root, 'Demo', PhotoSettings())
            for key in ('builtin/noir', '../demo', 'custom/../demo',
                        'custom/../../x', 'custom/x/y', 'custom/hello\\there',
                        'custom/.hidden', 'custom/demO!'):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    delete_preset(root, key)
            (root / 'photo-presets/demo.json').unlink()
            (root / 'photo-presets/demo.json').symlink_to(root / 'VERSION')
            with self.assertRaises(ValueError):
                delete_preset(root, user.key)
            self.assertTrue((root / 'photo-presets/demo.json').is_symlink())

    def test_bad_files_are_skipped_without_hiding_healthy_looks(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            good = save_preset(root, 'Good', PhotoSettings())
            directory = root / 'photo-presets'
            (directory / 'corrupt.json').write_text('{invalid json', encoding='utf-8')
            (directory / 'huge.json').write_bytes(b'x' * 4097)
            (directory / 'evil.json').symlink_to(directory / 'good.json')
            corrupted = json.loads((directory / 'good.json').read_text())
            corrupted['settings']['columns'] = True
            (directory / 'type-confusion.json').write_text(json.dumps(corrupted))
            items, skipped = list_presets(root)
            self.assertEqual(skipped, 4)
            self.assertEqual([x.key for x in items[-1:]], [good.key])
            directory2 = root / 'unsafe'
            directory2.mkdir()
            (root / 'photo-presets').rename(root / 'safe-original')
            (root / 'photo-presets').symlink_to(directory2, target_is_directory=True)
            with self.assertRaises(ValueError):
                save_preset(root, 'Do not escape', PhotoSettings())
            with self.assertRaises(ValueError):
                list_presets(root)
            self.assertEqual(list(directory2.iterdir()), [])

    def test_new_write_fails_safely_and_never_leaves_partial_preset(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            with patch('photo_presets.os.fsync', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    save_preset(root, 'Broken', PhotoSettings())
            self.assertEqual(list((root / 'photo-presets').iterdir()), [])
            self.assertEqual(list_presets(root), (list(BUILTIN_PRESETS), 0))

    def test_preset_does_not_change_conversion_engine_or_stored_recipe_schema(self):
        settings = BUILTIN_PRESETS[2].settings
        from photo_ascii import photo_to_ascii
        pixels = bytes([i % 256 for i in range(16 * 16 * 3)])
        result = photo_to_ascii(pixels, 16, 16, settings=settings)
        self.assertEqual(len(result.splitlines()), settings.rows)
        self.assertEqual(len(result.splitlines()[0]), settings.columns)


class PhotoPresetUIContracts(unittest.TestCase):
    def test_progressive_editor_actions_are_wired_and_no_implicit_export(self):
        view = (ROOT / 'photo_ascii_view.py').read_text()
        ast.parse(view)
        for code in ("Adw.PreferencesGroup(title='Start with a creative look'",
                     "self.personal_presets.set_expanded(False)",
                     "label='Apply Look'", "label='Save Preset'", "label='Remove'",
                     'def _apply_selected_preset(', 'def _save_custom_preset(',
                     'def _confirm_delete_preset(', 'def _remove_custom_preset(',
                     'self._apply_settings(preset.settings)',
                     'save_preset(self.config_dir, self.preset_name.get_text(), self._settings())',
                     'delete_preset(self.config_dir, key)',
                     "self._apply_settings(project.settings)"):
            self.assertIn(code, view)
        self.assertIn('self._refresh()', view)
        self.assertIn("dialog.set_default_response('cancel')", view)
        self.assertNotIn('subprocess', view)

    def test_version_installer_and_documentation(self):
        self.assertIn('photo_project photo_presets diagnostics_model', (ROOT / 'install.sh').read_text())
        self.assertGreaterEqual(int((ROOT / 'VERSION').read_text().strip().split('.')[1]), 91)
        self.assertIn(f'BUILD_VERSION = "{(ROOT / "VERSION").read_text().strip()}"', (ROOT / 'build_info.py').read_text())
        for name in ('TASKS.md', 'ROADMAP.md', 'CHANGELOG.md', 'RELEASE-V91.md'):
            self.assertIn('V91', (ROOT / name).read_text(), name)


if __name__ == '__main__':
    unittest.main()
