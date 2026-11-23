"""V75: playlist editor uses a gallery-first layout and independent filters."""
from _bootstrap import SRC, read_source  # noqa: F401
import ast
from pathlib import Path
import unittest

from playlist_engine import EFFECTS
from playlist_gallery_model import visible_effects, selection_caption

ROOT = Path(__file__).resolve().parents[1]


class GalleryModelTests(unittest.TestCase):
    def test_search_is_casefolded_and_whitespace_trimmed(self):
        self.assertEqual(visible_effects(EFFECTS, query='  RaIN '), ['rain'])
        self.assertEqual(visible_effects(EFFECTS, query='unfindable effect'), [])
        self.assertEqual(visible_effects(EFFECTS, query=''), EFFECTS)

    def test_duration_and_intensity_compose_with_search(self):
        self.assertEqual(visible_effects(EFFECTS, query='w', duration='long',
                                         intensity='gentle'), ['waves'])
        self.assertEqual(visible_effects(EFFECTS, query='matrix', duration='short'), [])
        self.assertEqual(visible_effects(EFFECTS, intensity='energetic',
                                         duration='long'), ['matrix', 'orbittingvolley',
                                                            'rings', 'swarm', 'thunderstorm'])

    def test_filter_does_not_erase_hidden_playlist_selection(self):
        selected = ['matrix', 'rain', 'waves']
        original = selected[:]
        filtered = visible_effects(EFFECTS, query='rain')
        self.assertEqual(filtered, ['rain'])
        self.assertEqual(selection_caption(selected, EFFECTS, len(filtered)),
                         f'3 of {len(EFFECTS)} selected · 1 shown')
        self.assertEqual(selected, original)
        self.assertEqual(selection_caption(['rain', 'rain', 'made-up'], EFFECTS, 0),
                         f'1 of {len(EFFECTS)} selected · 0 shown')


class GalleryFirstUiContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (SRC / 'playlist_editor.py').read_text()
        cls.tree = ast.parse(cls.source)

    def test_spare_window_height_belongs_to_effect_gallery(self):
        text = self.source
        self.assertIn('self.gallery_stack.set_vexpand(True)', text)
        self.assertIn('scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True, min_content_height=300)', text)
        self.assertLess(text.index('right.append(self.gallery_stack)'),
                        text.index('right.append(self.options_revealer)'))
        self.assertNotIn('right.append(generator_group)', text)
        self.assertNotIn('right.append(details)', text)
        self.assertIn('options_scroll.set_max_content_height(200)', text)
        self.assertIn('self.options_revealer = Gtk.Revealer()', text)
        self.assertIn('content_header.pack_end(self.options_button)', text)
        self.assertIn('self.options_revealer.set_reveal_child(button.get_active())', text)

    def test_gallery_search_empty_results_and_cards_use_single_hover_surface(self):
        text = self.source
        self.assertIn("self.search.connect('search-changed', self.refresh_effects)", text)
        self.assertIn("self.gallery_stack.add_named(empty, 'empty')", text)
        self.assertIn("'gallery' if matches else 'empty'", text)
        self.assertIn("toggle_thumbnail.add_css_class('playlist-thumbnail-action')", text)
        self.assertIn("tile.add_css_class('selected')", text)
        self.assertIn("tile.remove_css_class('selected')", text)
        self.assertIn("check.connect('toggled',self.toggle_effect,effect,tile)", text)
        self.assertIn('playlist-thumbnail-action:focus-visible', text)

    def test_sidebar_and_play_actions_retained(self):
        text = self.source
        self.assertIn("columns = Adw.NavigationSplitView()", text)
        self.assertIn("self.columns.set_show_content(True)", text)
        self.assertIn("play.connect('clicked', self._play_effect, effect)", text)
        self.assertIn("toggle_thumbnail.connect('clicked', self._toggle_effect_thumbnail, check)", text)
        self.assertIn('overlay.add_overlay(self.unsaved_banner)', text)
        self.assertIn("discard.connect(\"clicked\", self.discard)", text)
        self.assertIn("save.connect(\"clicked\", self.save)", text)

    def test_new_filter_module_is_shipped(self):
        installer = (ROOT / 'install.sh').read_text()
        self.assertIn('"$py_src/playlist_gallery_model.py"', installer)
        self.assertIn('from playlist_gallery_model import visible_effects, selection_caption', self.source)


if __name__ == '__main__':
    unittest.main()
