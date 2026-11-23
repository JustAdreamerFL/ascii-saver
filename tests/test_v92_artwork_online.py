"""V92 provider, explicit import, metadata migration and UI contract tests."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

from dataclasses import replace
import ast
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from artwork_catalog import (ArtworkMetadata, list_artworks, load_tags, load_metadata,
                             save_tags, save_metadata, filter_artworks)
from artwork_library import save_generated_artwork
from artwork_online import (SOURCE_URL, FEED_URL, LICENSE_NOTE, RemoteArtwork,
                            parse_collection, load_collection, import_remote,
                            filter_collection, top_tags, MAX_FEED_BYTES, _clean_line)

ROOT = Path(__file__).resolve().parents[1]

SAMPLE = ('  /\\\n /  \\\n/____\\\n'
          'tags: house, geometric\ndescription: Little cottage\n===EOF===\n'
          ' . .\n( o )\n `-`\ntags: organic, nature\n'
          'description: Watching forest\n===EOF===\n').encode('utf8')


class ProviderTests(unittest.TestCase):
    def test_parses_documented_feed_and_search_filters(self):
        items = parse_collection(SAMPLE)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].description, 'Little cottage')
        self.assertIn('house', items[0].tags)
        self.assertEqual(items[0].author, 'Unknown')
        self.assertEqual(items[0].source_url, SOURCE_URL)
        self.assertEqual(items[0].license, LICENSE_NOTE)
        self.assertEqual([a.title for a in filter_collection(items, 'forest', 'nature')], ['Watching forest'])
        self.assertEqual([a.number for a in filter_collection(items, '', 'geometric')], [1])
        self.assertEqual(top_tags(items), ['geometric', 'house', 'nature', 'organic'])
        self.assertEqual(filter_collection(items, 'doesnotexist'), [])

    def test_rejects_malformed_and_oversized_remote_content(self):
        for payload in (b'hello', b'===EOF===', b'\xff===EOF===', b'x'*(MAX_FEED_BYTES+1)):
            with self.subTest(payload=payload[:15]), self.assertRaises(ValueError):
                parse_collection(payload)
        self.assertNotIn('\x1b', _clean_line('banner\x1b[31mred\x1b[0m'))
        self.assertNotIn('[31m', _clean_line('banner\x1b[31mred\x1b[0m'))
        self.assertNotIn('\u202e', _clean_line('a\u202eb'))
        huge = ('*'*365 + '\n===EOF===\n').encode()
        with self.assertRaises(ValueError):
            parse_collection(huge)

    def test_cache_online_and_offline_fallback(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            items, status = load_collection(root, downloader=lambda: SAMPLE)
            self.assertEqual(len(items), 2)
            self.assertEqual(status, 'Live collection')
            self.assertEqual((root / 'online-cache/ascii-bin.txt').read_bytes(), SAMPLE)
            def offline():
                raise OSError('no network')
            saved, status = load_collection(root, downloader=offline)
            self.assertEqual(saved, items)
            self.assertIn('Offline cached', status)

    def test_no_cache_failure_and_cache_symlink_rejected(self):
        with TemporaryDirectory() as d, TemporaryDirectory() as elsewhere:
            root = Path(d)
            with self.assertRaises(ValueError):
                load_collection(root, downloader=lambda: (_ for _ in ()).throw(OSError('offline')))
            (root / 'online-cache').symlink_to(Path(elsewhere), target_is_directory=True)
            with self.assertRaises(ValueError):
                load_collection(root, downloader=lambda: (_ for _ in ()).throw(OSError('offline')))
            items, status = load_collection(root, downloader=lambda: SAMPLE)
            self.assertEqual(len(items), 2)
            self.assertIn('cache unavailable', status)
            self.assertEqual(list(Path(elsewhere).iterdir()), [])

    def test_import_with_attribution_and_no_overwriting(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            art = parse_collection(SAMPLE)[0]
            a = import_remote(root, art)
            b = import_remote(root, art)
            self.assertNotEqual(a, b)
            self.assertEqual((root / a).read_text(), art.artwork)
            meta = load_metadata(root, a)
            self.assertEqual(meta.tags, art.tags)
            self.assertEqual(meta.license, LICENSE_NOTE)
            self.assertEqual(meta.author, 'Unknown')
            self.assertEqual(meta.source_url, SOURCE_URL)
            self.assertIn('Little cottage', meta.description)
            entries, skipped = list_artworks(root)
            self.assertEqual(skipped, 0)
            self.assertEqual(len(filter_artworks(entries, 'unknown')), 2)
            self.assertEqual(len(filter_artworks(entries, 'cottage')), 2)

    def test_import_rejects_provider_spoof_and_rolls_back_metadata_failure(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            art = parse_collection(SAMPLE)[0]
            with self.assertRaises(ValueError):
                import_remote(root, replace(art, source_url='https://evil.example/test'))
            with patch('artwork_online.save_metadata', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    import_remote(root, art)
            self.assertEqual(list((root / 'artworks').iterdir()), [])


class MetadataTests(unittest.TestCase):
    def test_legacy_v1_metadata_is_loaded_and_upgraded_losslessly(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            ref = save_generated_artwork(root, 'legacy', '@@@\n')
            file = root / 'artwork-meta/legacy.json'
            file.parent.mkdir()
            file.write_text(json.dumps({'version': 1, 'artwork': ref, 'tags': ['Original']}))
            self.assertEqual(load_metadata(root, ref).tags, ('Original',))
            saved = save_metadata(root, ref, ArtworkMetadata(('Original',), 'Creator',
                        'An example', 'CC BY 4.0', 'https://example.org/work'))
            self.assertEqual(load_tags(root, ref), ('Original',))
            self.assertEqual(json.loads(file.read_text())['version'], 2)
            self.assertEqual(save_tags(root, ref, ['Other']), ('Other',))
            self.assertEqual(load_metadata(root, ref).author, 'Creator')
            self.assertEqual(load_metadata(root, ref).source_url, saved.source_url)

    def test_rejects_control_chars_invalid_links_and_unsafe_sidecars(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            ref = save_generated_artwork(root, 'safe', 'ok\n')
            original = (root / ref).read_bytes()
            for metadata in (ArtworkMetadata(author='x\ny'), ArtworkMetadata(source_url='http://example.org'),
                             ArtworkMetadata(source_url='https://user:password@example.org'),
                             ArtworkMetadata(description='x'*601)):
                with self.subTest(meta=metadata), self.assertRaises(ValueError):
                    save_metadata(root, ref, metadata)
            self.assertEqual((root / ref).read_bytes(), original)
            folder = root / 'artwork-meta'
            folder.mkdir(exist_ok=True)
            (folder / 'safe.json').symlink_to(root / ref)
            with self.assertRaises(ValueError):
                save_metadata(root, ref, ArtworkMetadata(author='A'))
            with self.assertRaises(ValueError):
                load_metadata(root, ref)
            (folder / 'safe.json').unlink()
            save_metadata(root, ref, ArtworkMetadata(author='Bob'))
            payload = json.loads((folder / 'safe.json').read_text())
            payload['tags'] = 'wrong type'
            (folder / 'safe.json').write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                load_metadata(root, ref)

    def test_optional_broken_metadata_does_not_hide_art(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            ref = save_generated_artwork(root, 'safe', 'OK\n')
            save_metadata(root, ref, ArtworkMetadata(author='Alice'))
            (root / 'artwork-meta/safe.json').write_text('{bad')
            results, skipped = list_artworks(root)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].tags, ())
            self.assertEqual(skipped, 1)


class UIAndPackageContracts(unittest.TestCase):
    def test_real_gallery_actions_and_responsive_layout(self):
        gallery = (SRC / 'artwork_library_view.py').read_text()
        online = (SRC / 'artwork_online_view.py').read_text()
        for source in (gallery, online):
            ast.parse(source)
        for text in ("Gtk.Button(label='Browse Online')", 'OnlineArtworkWindow(',
                     "Gtk.Button(label='Save Details')", 'save_metadata(',
                     'self._refresh(select_reference=reference)',
                     "narrow.add_setter(discovery_actions, 'orientation', Gtk.Orientation.VERTICAL)"):
            self.assertIn(text, gallery)
        for text in ('Thread(target=worker', 'GLib.idle_add(', 'load_collection(',
                     'filter_collection(', 'import_remote(', 'Adw.AlertDialog.new(',
                     "max-width: 730sp", 'self.preview = Gtk.TextView(', 'self.preview.get_buffer().set_text(item.artwork)'):
            self.assertIn(text, online)
        self.assertNotIn('subprocess', online)

    def test_installer_and_version(self):
        install = (ROOT / 'install.sh').read_text()
        self.assertIn('artwork_online artwork_online_view', install)
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertGreaterEqual(int(version.split('.')[1]), 92)
        self.assertIn(f'BUILD_VERSION = "{version}"', (SRC / 'build_info.py').read_text())
        for file in ('TASKS.md', 'ROADMAP.md', 'CHANGELOG.md', 'MASTER-BACKLOG.md', 'RELEASE-V92.md'):
            self.assertIn('V92', read_source(file))


if __name__ == '__main__':
    unittest.main()
