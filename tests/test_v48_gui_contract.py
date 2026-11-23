"""Regression contracts for user-reported V47 GUI bugs, no GTK import needed."""
from _bootstrap import SRC, read_source  # noqa: F401
from ui_sources import all_ui_source

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent

class PreviewGuiContract(unittest.TestCase):
    def test_vte_spawn_uses_keyword_signature_matching_main_renderer(self):
        source = (SRC / "preferences_gallery.py").read_text()
        tree = ast.parse(source)
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == 'spawn_async']
        self.assertEqual(1, len(calls))
        call = calls[0]
        self.assertEqual([], call.args, 'Positional VTE parameters caused cancellable to be treated as timeout')
        names = {keyword.arg for keyword in call.keywords}
        self.assertEqual({'pty_flags','working_directory','argv','envv','spawn_flags',
                          'child_setup','timeout','cancellable','callback','user_data'}, names)

    def test_live_preview_is_visible_without_scrolling_through_cards(self):
        source = all_ui_source()
        self.assertIn('gallery_shell.append(self.live_preview_revealer)', source)
        self.assertIn('gallery_shell.append(self.gallery_stack)', source)
        self.assertIn('self.gallery_stack.add_named(gallery_scroll, "gallery")', source)
        self.assertIn('self.live_preview_revealer.set_reveal_child(True)', source)
        self.assertIn('self.preview_title.set_text(f"Preview failed for {effect}: {error}")', source)

    def test_library_and_playlist_are_adjacent_in_sticky_toolbar(self):
        source = all_ui_source()
        self.assertIn('("Effect Library", "Browse", self._open_gallery)', source)
        self.assertIn('("Playlist Editor", "Open", self._open_playlist_editor)', source)
        self.assertIn('tools.append(tools_group)', source)
        self.assertIn('preview_page.append(preview_group)', source)
        self.assertIn('def _open_raw_playlist_editor', source)
        self.assertNotIn('content.append(gallery_row)', source)

    def test_unsaved_banner_does_not_relayout_page(self):
        source = all_ui_source()
        self.assertIn('toolbar_view.add_bottom_bar(self.changes_tray)', source)
        self.assertIn('self.changes_tray = self.unsaved_banner', source)
        self.assertNotIn('toolbar.append(self.unsaved_banner)', source)

    def test_preview_posters_are_decoded_one_frame_at_a_time(self):
        source = (SRC / 'animated_preview.py').read_text()
        self.assertIn('self.show_poster()', source)
        self.assertIn('self._set_frame_texture(pack, 0)', source)
        self.assertIn('pack.mask_frame(index)', source)
        self.assertIn('preview.set_playing(inside)', source)
        self.assertIn('self.set_paintable(None)', source)

if __name__ == '__main__': unittest.main()
