"""V47: all preview packs are bounded and independently decodable without GTK."""
from ui_sources import all_ui_source

import unittest
from pathlib import Path
from preview_asset import PackedPreview
from effect_selection import EFFECTS

ROOT = Path(__file__).resolve().parent.parent

class PackedPreviewTests(unittest.TestCase):
    def test_every_effect_has_readable_animation(self):
        for name in EFFECTS:
            with self.subTest(effect=name):
                p = ROOT / 'preview-packs' / f'{name}.aspr'
                self.assertTrue(p.is_file())
                with PackedPreview(p) as frames:
                    self.assertLessEqual(frames.width * frames.height * 4, 256 * 100 * 4)
                    self.assertLessEqual(frames.frame_count, 40)
                    self.assertNotEqual(frames.frame(0), frames.frame(frames.frame_count // 2))
                    self.assertTrue(all(delay >= 70 for delay in frames.delays))
                    with self.assertRaises(IndexError):
                        frames.frame(frames.frame_count)

    def test_gallery_releases_frames_on_close_and_scroll(self):
        source = all_ui_source()
        self.assertIn('for preview in self.effect_previews.values():', source)
        self.assertIn('preview.release()', source)
        self.assertIn('gallery_scroll.get_vadjustment().connect("value-changed"', source)
        self.assertIn('self._queue_gallery_sync()', source)
        editor = (ROOT / 'playlist_editor.py').read_text()
        self.assertIn('preview.release()', editor)
        self.assertIn('update_visible_previews(self.effect_scroller', editor)

    def test_unsaved_state_is_based_on_snapshot_and_slider_is_legible(self):
        source = all_ui_source()
        self.assertIn('self._preference_snapshot() != self._saved_snapshot', source)
        self.assertIn('self._saved_snapshot = self._preference_snapshot()', source)
        self.assertIn('self.background = Gtk.ColorDialogButton.new(', source)
        self.assertIn('slider.set_draw_value(True)', source)
        self.assertIn('slider.set_value_pos(Gtk.PositionType.RIGHT)', source)

if __name__ == '__main__':
    unittest.main()
