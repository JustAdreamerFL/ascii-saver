"""End-to-end headless tests of local asset indexing, metadata and safe reuse."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from artwork_catalog import (filter_artworks, list_artworks, load_tags, save_tags,
                             _orient, _safe_preview)
from artwork_library import save_generated_artwork
from artwork_templates import TEMPLATES
from photo_ascii import PhotoSettings
from photo_project import save_photo_project

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_lists_real_artwork_and_photo_assets_without_touching_them(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            text_ref = save_generated_artwork(root, 'Mountain Vista', '  /\\   /\\\n /  \\_/  \\\n')
            source = b'BM' + bytes(range(64))
            photo_ref = save_photo_project(root, 'Portrait sketch', 'x\nx\nx\nx\nx\nx\n',
                                           source, '.bmp', PhotoSettings())
            originals = {ref: (root / ref).read_bytes() for ref in (text_ref, photo_ref)}
            catalog, skipped = list_artworks(root)
            self.assertEqual(skipped, 0)
            self.assertEqual(len(catalog), 2)
            self.assertEqual({a.kind for a in catalog}, {'Text artwork', 'Photo project'})
            self.assertEqual({a.reference for a in catalog}, {text_ref, photo_ref})
            self.assertEqual([a.reference for a in filter_artworks(catalog, 'portrait')], [photo_ref])
            self.assertEqual([a.reference for a in filter_artworks(catalog, '', 'Photo project')], [photo_ref])
            self.assertEqual([a.reference for a in filter_artworks(catalog, 'mountain vista', 'Text artwork')], [text_ref])
            self.assertFalse(filter_artworks(catalog, 'missing'))
            self.assertEqual(originals, {ref: (root / ref).read_bytes() for ref in originals})

    def test_tags_roundtrip_are_searchable_and_do_not_modify_existing_ascii(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            ref = save_generated_artwork(root, 'Sun', ' .O.\n')
            original = (root / ref).read_bytes()
            self.assertEqual(save_tags(root, ref, [' Nocturne ', 'Liptov']), ('Nocturne', 'Liptov'))
            self.assertEqual(load_tags(root, ref), ('Nocturne', 'Liptov'))
            catalog, skipped = list_artworks(root)
            self.assertEqual(skipped, 0)
            self.assertEqual(filter_artworks(catalog, 'nocturne liptov')[0].reference, ref)
            self.assertEqual(save_tags(root, ref, []), ())
            self.assertEqual((root / ref).read_bytes(), original)

    def test_tag_validation_rejects_duplicates_controls_oversize_and_escaping(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            ref = save_generated_artwork(root, 'Art', '*\n')
            for invalid in (['a', 'A'], ['a\nb'], ['x'*25], [''], ['a,b'], ['a']*13):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    save_tags(root, ref, invalid)
            for invalid in ('logo.txt', '../logo.txt', 'artworks/../../other.txt', 'artworks/ghost.txt'):
                with self.subTest(reference=invalid), self.assertRaises(ValueError):
                    save_tags(root, invalid, ['tag'])
            self.assertEqual(load_tags(root, ref), ())

    def test_refuses_symlinks_and_broken_artwork_but_keeps_healthy_assets(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            ref = save_generated_artwork(root, 'Good', 'ok\n')
            (root / 'artworks/alias.txt').symlink_to(root / ref)
            (root / 'artworks/invalid.txt').write_bytes(b'\xff\xfe')
            (root / 'artworks/oversize.txt').write_bytes(b'a' * 2_000_001)
            catalog, skipped = list_artworks(root)
            self.assertEqual([a.reference for a in catalog], [ref])
            self.assertEqual(skipped, 3)
            with self.assertRaises(ValueError):
                save_tags(root, 'artworks/alias.txt', ['tag'])
            (root / 'artwork-meta').symlink_to(root / 'artworks', target_is_directory=True)
            with self.assertRaises(ValueError):
                save_tags(root, ref, ['tag'])
            (root / 'artwork-meta').unlink()
            save_tags(root, ref, ['good'])
            (root / 'artwork-meta/good.json').write_text('{bad data')
            catalog, skipped = list_artworks(root)
            self.assertEqual([a.reference for a in catalog], [ref])
            self.assertEqual(catalog[0].tags, ())
            self.assertEqual(skipped, 4)

    def test_rejects_tampered_metadata_and_manifest_mismatches(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            ref = save_generated_artwork(root, 'Test', 'hello\n')
            save_tags(root, ref, ['good'])
            file = root / 'artwork-meta/test.json'
            manifest = json.loads(file.read_text())
            for corruption in ({**manifest, 'artwork':'artworks/other.txt'},
                               {**manifest, 'version': True},
                               {**manifest, 'tags': ['evil\nline']}):
                file.write_text(json.dumps(corruption))
                with self.assertRaises(ValueError):
                    load_tags(root, ref)

    def test_empty_library_and_geometry_and_bounded_safe_preview(self):
        with TemporaryDirectory() as directory:
            self.assertEqual(list_artworks(Path(directory)), ([], 0))
        self.assertEqual(_orient(90, 20), 'Landscape')
        self.assertEqual(_orient(10, 35), 'Portrait')
        self.assertEqual(_orient(50, 30), 'Square')
        preview = _safe_preview('\n'.join(['long\x1b[31m' + 'x'*200]*45))
        self.assertLessEqual(len(preview.splitlines()), 33)
        self.assertNotIn('\x1b', preview)
        self.assertTrue(preview.endswith('…'))

    def test_copying_original_template_creates_separate_asset(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            template = TEMPLATES[0]
            first = save_generated_artwork(root, template.title, template.artwork)
            second = save_generated_artwork(root, template.title, template.artwork)
            self.assertNotEqual(first, second)
            self.assertEqual((root / first).read_text(), template.artwork)
            self.assertEqual((root / second).read_text(), template.artwork)


class CatalogUIContracts(unittest.TestCase):
    def test_gallery_wired_to_editor_with_accessible_actions(self):
        editor = (ROOT / 'artwork_editor.py').read_text()
        gallery = (ROOT / 'artwork_library_view.py').read_text()
        chooser = (ROOT / 'artwork_templates_view.py').read_text()
        for source in (editor, gallery, chooser):
            ast.parse(source)
        for text in ('library = Gtk.Button(label="My Artwork")',
                     'self._open_library', 'ArtworkLibraryWindow(self, self.config_dir)'):
            self.assertIn(text, editor)
        for text in ('Gtk.SearchEntry(', 'self.kind = Gtk.DropDown',
                     'self.orientation = Gtk.DropDown', 'self.preview = Gtk.TextView(editable=False',
                     "max-width: 730sp", 'save_metadata(self.config_dir, selected.reference, ArtworkMetadata(',
                     'save_generated_artwork(self.config_dir, template.title, template.artwork)',
                     'ArtworkEditor(parent, path, config_dir=self.config_dir,',
                     'self._opened_editors.get(ref)', 'self.open_button.set_sensitive(asset is not None)'):
            self.assertIn(text, gallery)
        self.assertIn('action_label="Use Template"', chooser)
        self.assertNotIn('subprocess', gallery)

    def test_install_and_docs_track_v90(self):
        self.assertIn('artwork_catalog artwork_library_view', (ROOT / 'install.sh').read_text())
        self.assertGreaterEqual(int((ROOT / 'VERSION').read_text().split('.')[1]), 90)
        self.assertIn(f'BUILD_VERSION = "{(ROOT / "VERSION").read_text().strip()}"', (ROOT / 'build_info.py').read_text())
        for filename in ('TASKS.md', 'ROADMAP.md', 'CHANGELOG.md', 'MASTER-BACKLOG.md', 'RELEASE-V90.md'):
            self.assertIn('V90', (ROOT / filename).read_text(), filename)


if __name__ == '__main__':
    unittest.main()
