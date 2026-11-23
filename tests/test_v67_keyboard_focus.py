"""GTK-free regression coverage for keyboard dismissal and initial focus.

The fake window model exercises the same startup path, without claiming a
compositor/Wayland integration test has happened.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest
from unittest.mock import Mock

SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def saver_method(name):
    tree = ast.parse(SOURCE)
    app = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "SaverApplication")
    method = next(n for n in app.body
                  if isinstance(n, ast.FunctionDef) and n.name == name)
    isolated = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(isolated)
    namespace = {}
    exec(compile(isolated, "app.py", "exec"), namespace)
    return namespace[name]


class MonitorModel:
    def __init__(self, items):
        self.items = items

    def get_n_items(self):
        return len(self.items)

    def get_item(self, index):
        return self.items[index]


class FakeApp:
    stopping = False
    windowed = False
    layer_shell = True
    shared_round = 0

    def __init__(self, monitors):
        self._monitors = MonitorModel(monitors)
        self.windows = []
        self.shared_finished = set()
        self.shared_pending = set()
        self.refresh_calls = 0
        self.advance_calls = 0

    def _overlay_windows(self):
        return self.windows

    def _refresh_keyboard_surface(self):
        self.refresh_calls += 1

    def _advance_when_all_ready(self):
        self.advance_calls += 1

    def _start_monitors_for_round(self, windows, round_number):
        pass  # Fake timer records the callback; this test only checks focus.


class KeyboardFocusTests(unittest.TestCase):
    def test_escape_action_is_registered_and_only_active_in_fullscreen(self):
        startup_source = ast.get_source_segment(SOURCE, next(
            node for node in ast.walk(ast.parse(SOURCE))
            if isinstance(node, ast.FunctionDef) and node.name == "do_startup"
        ))
        self.assertIn('Gio.SimpleAction.new("quit", None)', startup_source)
        self.assertIn('quit_action.connect("activate", self._on_quit_action)', startup_source)
        self.assertLess(startup_source.index('self.add_action(quit_action)'),
                        startup_source.index('self.set_accels_for_action("app.quit", ["Escape"])'))
        self.assertIn('if not self.windowed:', startup_source)

    def test_quit_action_calls_shutdown(self):
        app = Mock()
        saver_method("_on_quit_action")(app, None, None)
        app.quit_saver.assert_called_once_with()

    def test_only_primary_window_gets_keyboard_before_present(self):
        primary, secondary = object(), object()
        app = FakeApp([primary, secondary])
        seen = []

        def make_window(app_instance, monitor, windowed, keyboard_surface=False, defer_start=False):
            item = type("Window", (), {})()
            item.monitor = monitor
            item.windowed = windowed
            item.closing = False
            item.keyboard_surface = keyboard_surface
            app_instance.windows.append(item)
            seen.append((monitor, keyboard_surface))
            return item

        fn = saver_method("_sync_monitor_windows")
        fn.__globals__["SaverWindow"] = make_window
        fn.__globals__["GLib"] = Mock()
        fn(app)
        self.assertEqual(seen, [(primary, True), (secondary, False)])
        self.assertEqual(app.advance_calls, 1)

        # A new non-primary monitor must never steal exclusive keyboard focus.
        tertiary = object()
        app._monitors = MonitorModel([primary, secondary, tertiary])
        fn(app)
        self.assertEqual(seen[-1], (tertiary, False))

    def test_no_monitors_fallback_keeps_keyboard_interactive(self):
        app = FakeApp([])
        seen = []

        def make_window(_app, monitor, windowed, keyboard_surface=False, defer_start=False):
            seen.append((monitor, keyboard_surface))

        fn = saver_method("_sync_monitor_windows")
        fn.__globals__["SaverWindow"] = make_window
        fn.__globals__["GLib"] = Mock()
        fn(app)
        self.assertEqual(seen, [(None, True)])


if __name__ == "__main__":
    unittest.main()
