"""End-to-end headless contracts for editable, immutable-source photo projects."""
from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from photo_ascii import PhotoSettings
from photo_project import (load_photo_project, reference_for_artwork,
                           save_photo_project)

ROOT = Path(__file__).resolve().parents[1]
PHOTO = b'BM' + bytes(range(200))  # Library persistence is decoder-independent.
SETTINGS = PhotoSettings(columns=42, rows=24, fit='fit', brightness=30,
                         contrast=145, invert=True, ramp='Minimal',
                         gamma=1.6, edge=70, dither=True)


class ProjectPersistenceTests(unittest.TestCase):
    def test_roundtrip_keeps_exact_original_source_and_all_conversion_settings(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ref = save_photo_project(root, '  Forest at Dawn!  ', '...\n', PHOTO, '.bmp', SETTINGS)
            self.assertEqual(ref, 'artworks/forest-at-dawn.txt')
            self.assertEqual((root / ref).read_text(), '...\n')
            info = load_photo_project(root, ref)
            self.assertEqual(info.settings, SETTINGS)
            self.assertEqual(info.source_path.read_bytes(), PHOTO)
            self.assertFalse(info.text_modified)
            self.assertEqual(reference_for_artwork(root, root / ref), ref)
            self.assertIsNone(reference_for_artwork(root, root / 'artworks/missing.txt'))
            self.assertEqual(info.source_path.parent, root / 'photo-projects' / 'forest-at-dawn')
            self.assertEqual(json.loads((info.source_path.parent / 'project.json').read_text())['version'], 1)

    def test_second_export_is_a_new_variant_and_does_not_change_old_recipe(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            first = save_photo_project(root, 'Orbit', '@\n', PHOTO, '.bmp', SETTINGS)
            second = save_photo_project(root, 'Orbit', '#\n', PHOTO + b'2', '.bmp',
                                        replace(SETTINGS, columns=55))
            self.assertEqual((first, second), ('artworks/orbit.txt', 'artworks/orbit-2.txt'))
            self.assertEqual(load_photo_project(root, first).settings, SETTINGS)
            self.assertEqual(load_photo_project(root, second).settings.columns, 55)
            self.assertEqual((root / first).read_text(), '@\n')
            self.assertEqual((root / second).read_text(), '#\n')

    def test_collision_with_existing_plain_text_and_project_dir_is_safe(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'artworks').mkdir()
            (root / 'artworks/star.txt').write_text('original')
            (root / 'photo-projects/star-2').mkdir(parents=True)
            ref = save_photo_project(root, 'Star', 'new\n', PHOTO, '.bmp', SETTINGS)
            self.assertEqual(ref, 'artworks/star-3.txt')
            self.assertEqual((root / 'artworks/star.txt').read_text(), 'original')
            self.assertFalse((root / 'artworks/star-2.txt').exists())

    def test_manual_text_edits_are_detected_not_overwritten_by_reopening(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ref = save_photo_project(root, 'Editable', 'before\n', PHOTO, '.bmp', SETTINGS)
            (root / ref).write_text('hand drawn improvements\n')
            info = load_photo_project(root, ref)
            self.assertTrue(info.text_modified)
            self.assertEqual(info.source_path.read_bytes(), PHOTO)
            self.assertEqual((root / ref).read_text(), 'hand drawn improvements\n')

    def test_missing_modified_or_mismatched_source_refused(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ref = save_photo_project(root, 'Test', '#\n', PHOTO, '.bmp', SETTINGS)
            info = load_photo_project(root, ref)
            info.source_path.write_bytes(b'altered')
            with self.assertRaises(ValueError):
                load_photo_project(root, ref)
            info.source_path.write_bytes(PHOTO)
            manifest = info.source_path.parent / 'project.json'
            data = json.loads(manifest.read_text())
            data['artwork'] = '../elsewhere.txt'
            manifest.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_photo_project(root, ref)

    def test_json_settings_out_of_range_type_confusion_or_extra_fields_rejected(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ref = save_photo_project(root, 'Test', 'ok\n', PHOTO, '.bmp', SETTINGS)
            manifest = root / 'photo-projects/test/project.json'
            original = json.loads(manifest.read_text())
            for field, value in (('columns', 999), ('columns', True), ('gamma', 0.0),
                                 ('dither', 1), ('ramp', 'unknown')):
                with self.subTest(field=field, value=value):
                    changed = json.loads(json.dumps(original))
                    changed['settings'][field] = value
                    manifest.write_text(json.dumps(changed))
                    with self.assertRaises(ValueError):
                        load_photo_project(root, ref)
            original['settings']['unexpected'] = 1
            manifest.write_text(json.dumps(original))
            with self.assertRaises(ValueError):
                load_photo_project(root, ref)

    def test_unsupported_file_types_invalid_data_and_bad_reference_rejected(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for ext in ('../escape', '.exe', '.html', '.gif'):
                with self.subTest(ext=ext), self.assertRaises(ValueError):
                    save_photo_project(root, 'test', '@', PHOTO, ext, SETTINGS)
            for data in (b'', b'x' * (25_000_001)):
                with self.subTest(length=len(data)), self.assertRaises(ValueError):
                    save_photo_project(root, 'test', '@', data, '.png', SETTINGS)
            with self.assertRaises(ValueError):
                save_photo_project(root, 'test', '\x00', PHOTO, '.bmp', SETTINGS)
            with self.assertRaises(ValueError):
                save_photo_project(root, 'test', '@', PHOTO, '.bmp', replace(SETTINGS, gamma=99))
            for ref in ('../../secrets', 'artworks/../secrets.txt', '/etc/passwd'):
                with self.assertRaises(ValueError):
                    load_photo_project(root, ref)

    def test_refuses_symlinked_library_even_if_inside_root(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root / 'elsewhere'
            outside.mkdir()
            (root / 'artworks').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                save_photo_project(root, 'test', '@\n', PHOTO, '.bmp', SETTINGS)
            (root / 'artworks').unlink()
            (root / 'photo-projects').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                save_photo_project(root, 'test', '@\n', PHOTO, '.bmp', SETTINGS)
            self.assertEqual(list(outside.iterdir()), [])

    def test_rolls_back_project_and_artwork_when_file_write_fails(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for fail_on in (1, 2, 3):
                with self.subTest(fail_on=fail_on):
                    import os
                    real_fsync = os.fsync
                    calls = [0]
                    def break_at(fd):
                        calls[0] += 1
                        if calls[0] == fail_on:
                            raise OSError('disk full')
                        return real_fsync(fd)
                    with patch('os.fsync', side_effect=break_at):
                        with self.assertRaises(OSError):
                            save_photo_project(root, 'Failure', '@\n', PHOTO, '.bmp', SETTINGS)
                    self.assertEqual(list((root / 'photo-projects').iterdir()), [])
                    self.assertEqual(list((root / 'artworks').iterdir()), [])


class PhotoUIContractTests(unittest.TestCase):
    def test_editor_exposes_project_reopen_without_destroying_pending_photo_work(self):
        editor = (ROOT / 'artwork_editor.py').read_text()
        view = (ROOT / 'photo_ascii_view.py').read_text()
        ast.parse(editor)
        ast.parse(view)
        self.assertIn('reference_for_artwork(self.config_dir, path)', editor)
        self.assertIn('reopen = Gtk.Button(label="Reopen Photo")', editor)
        self.assertIn('def _reopen_photo(', editor)
        self.assertIn('if self._photo_window is not None:', editor)
        self.assertIn('saved_reference=self._saved_photo_reference', editor)
        self.assertIn('def _open_saved_project(', view)
        self.assertIn('load_photo_project(self.config_dir, reference)', view)
        self.assertIn('project.text_modified', view)
        self.assertIn('self._loading_project = True', view)
        self.assertIn('self._ensure_latest_preview()', view)
        self.assertIn('save_photo_project(self.config_dir, self.art_name.get_text()', view)
        self.assertNotIn('subprocess', view)

    def test_docs_version_and_installer_include_new_project_storage(self):
        self.assertIn('photo_project', (ROOT / 'install.sh').read_text())
        self.assertIn('diagnostics_model', (ROOT / 'install.sh').read_text())
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertGreaterEqual(int(version.split('.')[1]), 89)
        self.assertIn(f'BUILD_VERSION = "{version}"', (ROOT / 'build_info.py').read_text())
        for filename in ('CHANGELOG.md', 'TASKS.md', 'ROADMAP.md', 'RELEASE-V89.md'):
            self.assertIn('V89', (ROOT / filename).read_text(), filename)


if __name__ == '__main__':
    unittest.main()
