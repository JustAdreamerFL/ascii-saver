"""Regression checks for independent vs pinned library previews, without GTK."""
from ui_sources import all_ui_source

import ast
import json
import tempfile
from pathlib import Path
import unittest
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from helpers import DEFAULT_CONFIG, load_config


class PreviewModeTests(unittest.TestCase):
    def test_default_is_independent_window(self):
        self.assertEqual('window', DEFAULT_CONFIG['effect_preview_mode'])

    def test_config_roundtrip_and_invalid_value_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            for value in ('window', 'inline'):
                path.write_text(json.dumps({'effect_preview_mode': value}))
                self.assertEqual(value, load_config(path)['effect_preview_mode'])
            path.write_text(json.dumps({'effect_preview_mode': 'fullscreen-saver'}))
            self.assertEqual('window', load_config(path)['effect_preview_mode'])

    def test_mode_is_saved_compared_and_restored(self):
        source = all_ui_source()
        self.assertIn('"effect_preview_mode": (', source)
        self.assertIn('self.effect_preview_mode.get_selected(),', source)
        self.assertIn('self.effect_preview_mode.set_selected(', source)
        self.assertIn('self.library_preview_mode.set_selected(', source)
        self.assertIn('self.effect_preview_mode.connect("notify::selected", self._mark_dirty)', source)

    def test_dedicated_window_is_reused_and_does_not_route_through_screensaver(self):
        source = (ROOT / "preferences_gallery.py").read_text()
        tree = ast.parse(source)
        settings_class = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'GalleryControllerMixin')
        preview = next(x for x in settings_class.body if isinstance(x, ast.FunctionDef) and x.name == '_preview_effect')
        text = ast.get_source_segment(source, preview)
        self.assertIn('EffectPreviewWindow(self)', text)
        self.assertIn('self._effect_preview_window.play(', text)
        self.assertIn('self.effect_preview_mode.get_selected() == 0', text)
        self.assertNotIn('self._on_command', text)
        self.assertIn('self.preview_area.set_child(host)', text)

    def test_preview_survives_library_close_and_has_manual_close(self):
        source = (ROOT / "preferences_gallery.py").read_text()
        tree = ast.parse(source)
        settings_class = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'GalleryControllerMixin')
        close_gallery = next(x for x in settings_class.body if isinstance(x, ast.FunctionDef) and x.name == '_close_gallery')
        text = ast.get_source_segment(source, close_gallery)
        self.assertNotIn('_effect_preview_window.close()', text)
        self.assertIn('self.gallery_window.hide()', text)
        separate = (ROOT / 'effect_preview_window.py').read_text()
        self.assertIn('self.set_default_size(1100, 660)', separate)
        self.assertNotIn("close.connect('clicked', lambda *_: self.close())", separate)
        self.assertIn("replay.connect('clicked', self._replay)", separate)
        self.assertIn("self.connect('close-request', self._close_requested)", separate)
        self.assertNotIn("'key-pressed'", separate)
        self.assertNotIn("'motion'", separate)

    def test_inline_process_lifecycle_is_bounded(self):
        source = all_ui_source()
        self.assertIn('self._effect_preview_pid = pid', source)
        self.assertIn('os.kill(pid, signal.SIGTERM)', source)
        self.assertIn('gallery_shell.append(self.live_preview_revealer)', source)

if __name__ == '__main__':
    unittest.main()
