"""Headless behavioral regressions for Artwork Studio photo conversion V87."""
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from photo_ascii import PhotoSettings, RAMPS, photo_to_ascii
from artwork_library import save_generated_artwork

ROOT = Path(__file__).resolve().parents[1]


def rgb(width, height, pixel):
    return bytes(component for y in range(height) for x in range(width)
                 for component in pixel(x, y))


class PhotoConversionTests(unittest.TestCase):
    def setUp(self):
        self.black = rgb(8, 8, lambda _x, _y: (0, 0, 0))
        self.white = rgb(8, 8, lambda _x, _y: (255, 255, 255))
        self.opts = PhotoSettings(columns=16, rows=8)

    def test_black_and_white_mapping_and_inversion(self):
        dark = photo_to_ascii(self.black, 8, 8, settings=self.opts)
        light = photo_to_ascii(self.white, 8, 8, settings=self.opts)
        self.assertEqual(dark, ('@' * 16 + '\n') * 8)
        self.assertEqual(light, (' ' * 16 + '\n') * 8)
        inverted = photo_to_ascii(self.black, 8, 8, settings=replace(self.opts, invert=True))
        self.assertEqual(inverted, light)

    def test_ramp_and_basic_tuning_change_output(self):
        mid = rgb(8, 8, lambda _x, _y: (110, 110, 110))
        low = photo_to_ascii(mid, 8, 8, settings=self.opts)
        high = photo_to_ascii(mid, 8, 8, settings=replace(self.opts, brightness=70))
        self.assertNotEqual(low, high)
        self.assertEqual(high, (' ' * 16 + '\n') * 8)
        self.assertNotEqual(photo_to_ascii(mid, 8, 8, settings=replace(self.opts, contrast=0)), low)
        for name in RAMPS:
            art = photo_to_ascii(mid, 8, 8, settings=replace(self.opts, ramp=name))
            self.assertEqual(len(art.splitlines()), 8)
            self.assertEqual({len(x) for x in art.splitlines()}, {16})
            self.assertTrue(all(set(line) <= set(RAMPS[name]) for line in art.splitlines()))

    def test_crop_versus_fit_and_aspect_ratio(self):
        # Very wide photo: padded fit introduces actual blank lines; centered
        # crop fills the target canvas without padding.
        wide = rgb(60, 10, lambda _x, _y: (0, 0, 0))
        fitted = photo_to_ascii(wide, 60, 10, settings=replace(self.opts, fit='fit'))
        cropped = photo_to_ascii(wide, 60, 10, settings=replace(self.opts, fit='crop'))
        self.assertEqual(fitted.splitlines()[0], ' ' * 16)
        self.assertIn('@', fitted)
        self.assertEqual(cropped, ('@' * 16 + '\n') * 8)
        # Very tall photo: fitting adds whitespace on the two sides instead.
        tall = rgb(10, 70, lambda _x, _y: (0, 0, 0))
        output = photo_to_ascii(tall, 10, 70, settings=replace(self.opts, fit='fit'))
        self.assertEqual(output.splitlines()[0][0], ' ')
        self.assertIn('@', output)

    def test_rgba_is_composited_onto_white_and_row_padding_ignored(self):
        opaque = bytes([0, 0, 0, 255] * 8 * 8)
        transparent = bytes([0, 0, 0, 0] * 8 * 8)
        self.assertEqual(photo_to_ascii(opaque, 8, 8, channels=4, settings=self.opts),
                         ('@' * 16 + '\n') * 8)
        self.assertEqual(photo_to_ascii(transparent, 8, 8, channels=4, settings=self.opts),
                         (' ' * 16 + '\n') * 8)
        padded = b''.join(b'\x00' * 8 * 3 + b'\xff' * 4 for _ in range(8))
        self.assertEqual(photo_to_ascii(padded, 8, 8, rowstride=28, settings=self.opts),
                         ('@' * 16 + '\n') * 8)

    def test_invalid_inputs_rejected_before_access(self):
        bad = [dict(width=0, height=8), dict(width=8, height=5000),
               dict(width=8, height=8, channels=2),
               dict(width=8, height=8, rowstride=10)]
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                photo_to_ascii(self.black, **args)
        with self.assertRaises(ValueError):
            photo_to_ascii(b'\0', 8, 8)
        for opts in (replace(self.opts, columns=121), replace(self.opts, rows=1),
                     replace(self.opts, ramp='shell'), replace(self.opts, fit='stretch'),
                     replace(self.opts, brightness=101), replace(self.opts, cell_aspect=0)):
            with self.subTest(opts=opts), self.assertRaises(ValueError):
                photo_to_ascii(self.black, 8, 8, settings=opts)


class AssetExportTests(unittest.TestCase):
    def test_new_files_are_uniquely_named_and_existing_files_untouched(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            library = root / 'artworks'
            library.mkdir()
            (library / 'sunrise.txt').write_text('original\n')
            one = save_generated_artwork(root, 'Sunrise!', 'new art\n')
            two = save_generated_artwork(root, 'Sunrise!', 'second piece\n')
            self.assertEqual(one, 'artworks/sunrise-2.txt')
            self.assertEqual(two, 'artworks/sunrise-3.txt')
            self.assertEqual((library / 'sunrise.txt').read_text(), 'original\n')
            self.assertEqual((root / two).read_text(), 'second piece\n')

    def test_dangerous_names_cannot_escape_library(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = save_generated_artwork(root, '../../my secret/name.txt', 'ok\n')
            self.assertTrue(reference.startswith('artworks/'))
            self.assertNotIn('..', reference)
            self.assertEqual((root / reference).read_text(), 'ok\n')
            blank = save_generated_artwork(root, '___', 'x\n')
            self.assertEqual(blank, 'artworks/photo-art.txt')
            self.assertEqual(list(root.glob('*.txt')), [])

    def test_refuse_malformed_assets_and_external_symlink(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / 'config'
            root.mkdir()
            other = Path(tmp) / 'outside'
            other.mkdir()
            (root / 'artworks').symlink_to(other, target_is_directory=True)
            with self.assertRaises(ValueError):
                save_generated_artwork(root, 'test', 'hi')
            self.assertEqual(list(other.iterdir()), [])
            (root / 'artworks').unlink()
            with self.assertRaises(ValueError):
                save_generated_artwork(root, 'bad', '\0')
            with self.assertRaises(ValueError):
                save_generated_artwork(root, 'bad', 'x' * 2_000_001)

    def test_failed_save_cleans_up_own_partial_file(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch('os.fsync', side_effect=OSError('no space')):
                with self.assertRaises(OSError):
                    save_generated_artwork(root, 'failure', 'content\n')
            self.assertFalse((root / 'artworks' / 'failure.txt').exists())


class PhotoUIContracts(unittest.TestCase):
    def test_application_is_wired_and_adaptive_without_auto_writes(self):
        editor = (ROOT / 'artwork_editor.py').read_text()
        view = (ROOT / 'photo_ascii_view.py').read_text()
        for name, source in (('artwork_editor.py', editor), ('photo_ascii_view.py', view)):
            ast.parse(source, filename=name)
        self.assertIn('photo.connect("clicked", self._open_photo)', editor)
        self.assertIn('self._confirm_photo_replace(template, window)', editor)
        self.assertIn('def _photo_closed', editor)
        self.assertIn('self._photo_window.close()', editor)
        self.assertIn('Adw.BreakpointCondition.parse(\'max-width: 770sp\')', view)
        self.assertIn("narrow.add_setter(compare, 'orientation', Gtk.Orientation.VERTICAL)", view)
        self.assertIn('self.photo.set_pixbuf(pixbuf)', view)
        self.assertIn('self.preview.get_buffer().set_text(artwork)', view)
        self.assertIn('self._on_use(self._artwork, self)', view)
        self.assertIn('save_photo_project(self.config_dir', view)
        self.assertIn('GLib.timeout_add(80, self._refresh)', view)
        self.assertIn('self._ensure_latest_preview()', view)
        self.assertIn('GLib.source_remove(self._refresh_id)', view)
        self.assertNotIn('subprocess', view)
        self.assertNotIn('save_artwork(', view)

    def test_installer_and_docs_record_real_scope(self):
        installer = (ROOT / 'install.sh').read_text()
        self.assertIn('photo_ascii photo_ascii_view', installer)
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertRegex(version, r'^0\.\d+\.0$')
        self.assertIn(f'BUILD_VERSION = "{version}"', (ROOT / 'build_info.py').read_text())
        self.assertIn('## 0.87.0 (experimental) - 2026-11-08',
                      (ROOT / 'CHANGELOG.md').read_text())
        for doc in ('ROADMAP.md', 'TASKS.md', 'RELEASE-V87.md'):
            self.assertIn('Photo to ASCII', (ROOT / doc).read_text())


if __name__ == '__main__':
    unittest.main()
