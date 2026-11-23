"""V95 online discovery: bounded browsing, sorting, shuffle, safe refresh UI."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
from dataclasses import replace
from pathlib import Path
import unittest

from artwork_online import (PAGE_SIZE, SORT_OPTIONS, RemoteArtwork,
                            filter_collection, parse_collection, sort_collection)

ROOT = Path(__file__).resolve().parents[1]


class SortingAndDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.assets = tuple(RemoteArtwork(
            number=i + 1,
            title=f'Z{i % 4} {305 - i:03d}',
            description='Creative text',
            tags=('waves',) if i % 2 else ('space',),
            artwork='*' * (i % 15 + 1) + '\n',
            preview='*',
            columns=i % 15 + 1,
            rows=i % 6 + 1,
            orientation='Landscape' if i % 3 else 'Portrait',
        ) for i in range(305))

    def test_repository_default_is_unchanged(self):
        original = list(self.assets)
        self.assertEqual(sort_collection(self.assets), original)
        self.assertEqual(self.assets, tuple(original))
        self.assertEqual(PAGE_SIZE, 48)
        self.assertEqual(len(SORT_OPTIONS), 5)

    def test_size_and_title_sorts_keep_unique_items_and_ties_stable(self):
        for mode in ('Title A–Z', 'Smallest first', 'Largest first'):
            ordered = sort_collection(self.assets, mode)
            self.assertEqual(len(ordered), len(self.assets))
            self.assertEqual({a.number for a in ordered}, set(range(1, 306)))
            self.assertEqual(len({a.number for a in ordered}), 305)
            if mode == 'Title A–Z':
                self.assertEqual(ordered, sorted(self.assets, key=lambda a: (a.title.casefold(), a.number)))
            else:
                key = lambda a: a.columns * a.rows
                areas = list(map(key, ordered))
                self.assertEqual(areas, sorted(areas, reverse=mode == 'Largest first'))
        with self.assertRaises(ValueError):
            sort_collection(self.assets, 'Most popular')

    def test_seeded_shuffle_is_reproducible_and_not_repository_order(self):
        a = sort_collection(self.assets, 'Shuffle', seed=123)
        b = sort_collection(self.assets, 'Shuffle', seed=123)
        c = sort_collection(self.assets, 'Shuffle', seed=456)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, list(self.assets))
        self.assertEqual({x.number for x in a}, {x.number for x in self.assets})

    def test_filter_then_page_has_no_missing_or_repeated_results(self):
        selected = sort_collection(filter_collection(self.assets, 'Creative', 'waves'),
                                   'Shuffle', seed=999)
        batches = [selected[i:i + PAGE_SIZE] for i in range(0, len(selected), PAGE_SIZE)]
        self.assertTrue(all(0 < len(batch) <= PAGE_SIZE for batch in batches))
        flattened = [x.number for batch in batches for x in batch]
        self.assertEqual(flattened, [x.number for x in selected])
        self.assertEqual(len(set(flattened)), len(selected))

    def test_whitespace_in_remote_art_is_preserved_at_start(self):
        data = b'       /\\\n      /__\\\ntags: mountain\ndescription: A peak\n===EOF===\n'
        art = parse_collection(data)[0]
        self.assertTrue(art.artwork.startswith('       /\\'))
        self.assertEqual(sort_collection((art,), 'Shuffle', seed=10)[0].artwork, art.artwork)


class OnlineViewContracts(unittest.TestCase):
    def test_refresh_is_single_flight_and_preserves_in_memory_gallery(self):
        source = (SRC / 'artwork_online_view.py').read_text()
        tree = ast.parse(source)
        refresh = next(node for c in tree.body if isinstance(c, ast.ClassDef) and c.name == 'OnlineArtworkWindow'
                       for node in c.body if isinstance(node, ast.FunctionDef) and node.name == '_refresh')
        guarded = ast.get_source_segment(source, refresh.body[0])
        self.assertIn('self._closed or self._loading', guarded)
        self.assertIn('Showing last loaded collection.', source)
        self.assertIn('self.refresh_button.set_sensitive(False)', source)
        self.assertIn('self.refresh_button.set_sensitive(True)', source)

    def test_filters_sort_paged_render_no_auto_download_or_implicit_import(self):
        source = (SRC / 'artwork_online_view.py').read_text()
        ast.parse(source)
        for expected in ('Gtk.DropDown.new_from_strings(list(SORT_OPTIONS))',
                         "Gtk.Button(label='Surprise Me')",
                         "Gtk.Button(label='Show More Artwork')",
                         'self._visible_count = min(PAGE_SIZE, len(self._matches))',
                         'self._append_rows(self._matches[:self._visible_count])',
                         'self._matches[self._visible_count:next_count]',
                         "breakpoint.add_setter(controls, 'orientation', Gtk.Orientation.VERTICAL)",
                         "breakpoint.add_setter(panels, 'orientation', Gtk.Orientation.VERTICAL)",
                         'sort_collection(matches', 'self.preview.get_buffer().set_text(item.artwork)',
                         'if item is None or self._loading:',
                         "'The repository claims CC0, but individual creators and reuse rights are not verified. '"):
            self.assertIn(expected, source)
        self.assertNotIn('subprocess', source)

    def test_package_version_and_task_tracking(self):
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertGreaterEqual(tuple(map(int, version.split('.'))), (0, 95, 0))
        self.assertIn(f'BUILD_VERSION = "{version}"', (SRC / 'build_info.py').read_text())
        for file in ('ROADMAP.md', 'TASKS.md', 'CHANGELOG.md', 'MASTER-BACKLOG.md', 'RELEASE-V95.md'):
            self.assertIn('V95', read_source(file), file)


if __name__ == '__main__':
    unittest.main()
