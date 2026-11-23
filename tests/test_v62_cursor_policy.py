"""Regression checks for GNOME Wayland pointer hiding, no GTK required."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CursorPolicyTests(unittest.TestCase):
    def test_named_blank_cursor_before_texture_fallback(self):
        code = (ROOT / 'app.py').read_text()
        self.assertIn('Gdk.Cursor.new_from_name("none", None)', code)
        self.assertIn('Gdk.Cursor.new_from_texture(texture, 0, 0, None)', code)
        self.assertLess(code.index('Gdk.Cursor.new_from_name("none", None)'),
                        code.index('Gdk.Cursor.new_from_texture(texture, 0, 0, None)'))

    def test_handlers_connected_before_present(self):
        code = (ROOT / 'app.py').read_text()
        start = code.index('        self.connect("close-request", self._on_close)')
        end = code.index('        GLib.timeout_add(350, self._start)', start)
        region = code[start:end]
        self.assertLess(region.index('self.connect("map", self._on_mapped_for_cursor)'),
                        region.index('self.present()'))
        self.assertIn('self.connect("realize", self._on_mapped_for_cursor)', region)

    def test_cursor_on_pointer_and_surface(self):
        code = (ROOT / 'app.py').read_text()
        self.assertIn('motion.connect("enter", self._on_pointer_enter)', code)
        self.assertIn('self.terminal.set_cursor(self._invisible_cursor)', code)
        self.assertIn('surface.set_device_cursor(pointer, self._invisible_cursor)', code)

    def test_preview_does_not_hide_cursor(self):
        code = (ROOT / 'app.py').read_text()
        self.assertIn('def _hide_cursor(self) -> None:\n        if self.windowed:\n            return', code)

if __name__ == '__main__':
    unittest.main()
