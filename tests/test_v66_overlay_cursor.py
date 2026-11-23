"""Regression checks for GTK/VTE pointer overlay without GNOME Shell.

The target runtime must still be verified under live GNOME/Mutter. These tests
are source-level because CI has no GTK4/VTE display; the input/cursor strategy
was independently verified by the user's GTK4 overlay test on GNOME Wayland.
"""
from _bootstrap import SRC, read_source  # noqa: F401
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (SRC / 'app.py').read_text(encoding='utf-8')


class OverlayCursorTests(unittest.TestCase):
    @staticmethod
    def window_initializer():
        module = ast.parse(SOURCE)
        window = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'SaverWindow')
        initializer = next(n for n in window.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
        return ast.get_source_segment(SOURCE, initializer)

    def test_overlay_only_for_fullscreen_not_windowed_preview(self):
        source = self.window_initializer()
        self.assertIn('if windowed:\n            toolbar = Adw.ToolbarView()', source)
        self.assertIn('else:\n            self.cursor_overlay = Gtk.Overlay()', source)
        self.assertIn('self.cursor_overlay.set_child(self.terminal)', source)
        self.assertIn('self.cursor_overlay.add_overlay(self.cursor_catcher)', source)
        self.assertIn('self.set_content(self.cursor_overlay)', source)

    def test_catcher_covers_entire_terminal_and_is_targetable(self):
        source = self.window_initializer()
        for expected in (
            'self.cursor_catcher = Gtk.DrawingArea()',
            'self.cursor_catcher.set_halign(Gtk.Align.FILL)',
            'self.cursor_catcher.set_valign(Gtk.Align.FILL)',
            'self.cursor_catcher.set_can_target(True)',
            'self.cursor_catcher.set_can_focus(False)',
        ):
            self.assertIn(expected, source)

    def test_cursor_reapplied_to_catcher_after_map(self):
        self.assertIn('self.cursor_catcher.set_cursor(self._invisible_cursor)', SOURCE)
        self.assertIn('self.cursor_overlay.set_cursor(self._invisible_cursor)', SOURCE)
        self.assertIn('self.connect("map", self._on_mapped_for_cursor)', SOURCE)
        self.assertIn('motion.connect("enter", self._on_pointer_enter)', SOURCE)

    def test_parent_captures_input_without_dismissing_preview(self):
        source = self.window_initializer()
        self.assertIn('motion.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)', source)
        self.assertIn('motion.connect("motion", self._dismiss)', source)
        self.assertIn('key.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)', source)
        self.assertIn('click.connect("pressed", self._dismiss)', source)
        self.assertIn('scroll.connect("scroll", self._dismiss)', source)
        self.assertIn('if self.windowed:\n            # Preview stays open on ordinary input.', SOURCE)

    def test_shell_extension_not_needed_by_default(self):
        self.assertIn('os.environ.get("ASCII_SAVER_GNOME_CURSOR_BRIDGE") == "1"', SOURCE)
        self.assertIn('enabled=(not self.windowed and self._screen_lock_backend == GNOME', SOURCE)

    def test_versioned_build_matches_manifest(self):
        from build_info import BUILD_VERSION
        self.assertEqual(BUILD_VERSION, (ROOT / 'VERSION').read_text().strip())
        self.assertGreaterEqual(tuple(map(int, BUILD_VERSION.split('.'))), (0, 67, 0))


if __name__ == '__main__':
    unittest.main()
