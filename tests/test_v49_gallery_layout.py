"""Protect against V48's narrow-strip gallery regression without GTK access."""
from _bootstrap import SRC, read_source  # noqa: F401
from ui_sources import all_ui_source

from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parent.parent


class GalleryLayoutTests(unittest.TestCase):
    def test_library_has_genuine_expanding_scroll_region(self):
        s = all_ui_source()
        self.assertIn('gallery_scroll.set_vexpand(True)', s)
        self.assertIn('gallery_scroll.set_hexpand(True)', s)
        self.assertIn('gallery_scroll.set_min_content_height(320)', s)
        self.assertIn('gallery_shell.set_vexpand(True)', s)
        self.assertIn('gallery_shell.append(gallery_header)', s)
        self.assertIn('gallery_scroll.set_child(effect_grid)', s)
        self.assertNotIn('gallery_scroll.set_child(effect_frame)', s)

        # The controls must not be part of the scrolled grid.
        pos_header = s.index('gallery_shell.append(gallery_header)')
        pos_scroll = s.index('gallery_shell.append(self.gallery_stack)')
        pos_preview = s.index('gallery_shell.append(self.live_preview_revealer)')
        self.assertLess(pos_header, pos_scroll)
        self.assertLess(pos_scroll, pos_preview)

    def test_live_preview_is_bounded_and_uses_scrolled_window_child(self):
        s = all_ui_source()
        self.assertIn('self.preview_area.set_max_content_height(280)', s)
        self.assertIn('self.preview_area.set_vexpand(False)', s)
        self.assertIn('self.preview_area.set_child(host)', s)
        self.assertIn('self.preview_area.set_child(None)', s)
        self.assertNotIn('self.preview_area.append(terminal)', s)

    def test_playlist_thumbnail_click_toggles_and_play_is_separate(self):
        s = (SRC / 'playlist_editor.py').read_text()
        self.assertIn("toggle_thumbnail.connect('clicked', self._toggle_effect_thumbnail, check)", s)
        self.assertIn("play.connect('clicked', self._play_effect, effect)", s)
        self.assertIn('checkbox.set_active(not checkbox.get_active())', s)
        self.assertIn('toggle_thumbnail.set_child(preview)', s)
        self.assertIn('self.live_preview_window.play(effect,', s)
        self.assertNotIn("'destroy',", s)

    def test_preview_launcher_uses_vte_keyword_arguments_and_installs(self):
        source = (SRC / 'effect_preview_window.py').read_text()
        tree = ast.parse(source)
        calls = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                 and node.func.attr == 'spawn_async']
        self.assertEqual(1, len(calls))
        self.assertEqual([], calls[0].args)
        self.assertIn('timeout', {kw.arg for kw in calls[0].keywords})
        self.assertIn('cancellable', {kw.arg for kw in calls[0].keywords})
        install = (ROOT / 'install.sh').read_text()
        self.assertIn('"$py_src/effect_preview_window.py"', install)


if __name__ == '__main__':
    unittest.main()
