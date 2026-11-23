"""V104: shared GTK timer, hotplug cohorts and palette round safety."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest
from types import SimpleNamespace

from palette_engine import palette_color_for_round

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")


def method(name, cls="SaverApplication"):
    root = ast.parse(SOURCE)
    obj = next(x for x in root.body if isinstance(x, ast.ClassDef) and x.name == cls)
    fn = next(x for x in obj.body if isinstance(x, ast.FunctionDef) and x.name == name)
    module = ast.Module(body=[fn], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = {}
    exec(compile(module, "app.py", "exec"), scope)
    return scope[name]


class FakeGLib:
    SOURCE_REMOVE = False

    def __init__(self):
        self.queue = []
        self.batch = 0

    def timeout_add(self, ms, fn, *args):
        self.queue.append((ms, fn, args))
        return len(self.queue)

    def drain(self):
        pending, self.queue = self.queue, []
        self.batch += 1
        for _, callback, args in pending:
            callback(*args)


GLIB = FakeGLib()
START = method("_start_monitors_for_round")
ADVANCE = method("_advance_when_all_ready")
SYNC = method("_sync_monitor_windows")
START.__globals__["GLib"] = GLIB
ADVANCE.__globals__.update(GLib=GLIB, TTE_SUCCESS_RESTART_MS=80)
SYNC.__globals__["GLib"] = GLIB


class Monitor:
    def __init__(self, name):
        self.name = name

    def get_connector(self):
        return self.name


class MonitorModel:
    def __init__(self, monitors):
        self.monitors = monitors

    def get_item(self, i):
        return self.monitors[i]

    def get_n_items(self):
        return len(self.monitors)


class Window:
    def __init__(self, app, monitor, windowed, *, keyboard_surface=False,
                 defer_start=False):
        self.app = app
        self.monitor = monitor
        self.windowed = windowed
        self.closing = False
        self.running = False
        self.deferred = defer_start
        self.started = []
        app.windows.append(self)

    def _start(self):
        if self.running or self.closing:
            return False
        self.running = True
        self.started.append((GLIB.batch, self.app.shared_round,
                             palette_color_for_round(self.app.config,
                                 self.monitor.name if self.monitor else "default",
                                 self.app.shared_round)))
        return False


SYNC.__globals__["SaverWindow"] = Window


class App:
    def __init__(self, monitors):
        self.windows = []
        self._monitors = MonitorModel(monitors)
        self.layer_shell = False
        self.stopping = False
        self.windowed = False
        self.shared_round = 0
        self.shared_pending = set()
        self.shared_finished = set()
        self.config = {
            "playlist_mode": False, "cycle_palette": True,
            "palette_ping_pong": True, "palette_steps": 1,
            "palette": ["#FF0000", "#00FF00", "#0000FF"],
            "per_monitor_visuals": True,
            "monitor_visuals": {
                "DP-1": {"palette": ["#111111", "#222222", "#333333"]},
                "HDMI-1": {"palette": ["#AAAAAA", "#BBBBBB", "#CCCCCC"]},
            },
        }

    def _overlay_windows(self):
        return self.windows

    def _refresh_keyboard_surface(self):
        pass

    def _close_overlay_window(self, window):
        window.closing = True
        self.windows.remove(window)

    def _advance_when_all_ready(self):
        return ADVANCE(self)

    def _start_monitors_for_round(self, windows, round_number):
        return START(self, windows, round_number)


class MonitorCohortTests(unittest.TestCase):
    def setUp(self):
        GLIB.queue.clear()
        GLIB.batch = 0
        self.a = Monitor("DP-1")
        self.b = Monitor("HDMI-1")
        self.app = App([self.a, self.b])

    def test_first_two_monitors_share_a_single_timer_and_dispatch(self):
        SYNC(self.app)
        self.assertEqual(len(self.app.windows), 2)
        self.assertEqual(len(GLIB.queue), 1)
        self.assertEqual(GLIB.queue[0][0], 350)
        self.assertTrue(all(w.deferred for w in self.app.windows))
        GLIB.drain()
        self.assertEqual([w.started[0][0] for w in self.app.windows], [1, 1])
        self.assertEqual([w.started[0][1] for w in self.app.windows], [0, 0])
        self.assertEqual([w.started[0][2] for w in self.app.windows],
                         ["#111111", "#AAAAAA"])

    def test_advance_dispatches_one_timer_with_same_next_palette_round(self):
        SYNC(self.app)
        GLIB.drain()
        for window in self.app.windows:
            window.running = False
        self.app.shared_finished.update(self.app.windows)
        ADVANCE(self.app)
        self.assertEqual(self.app.shared_round, 1)
        self.assertEqual(len(GLIB.queue), 1)
        self.assertEqual(GLIB.queue[0][0], 80)
        GLIB.drain()
        self.assertEqual([w.started[-1][1] for w in self.app.windows], [1, 1])
        self.assertEqual([w.started[-1][2] for w in self.app.windows],
                         ["#222222", "#BBBBBB"])

    def test_obsolete_start_timer_never_starts_the_wrong_palette_round(self):
        SYNC(self.app)
        self.app.shared_round = 1
        GLIB.drain()
        self.assertEqual([w.started for w in self.app.windows], [[], []])
        START(self.app, tuple(self.app.windows), 1)
        self.assertEqual([w.started[0][1] for w in self.app.windows], [1, 1])

    def test_unplugged_monitor_not_started_by_a_queued_timer(self):
        SYNC(self.app)
        previous = self.app.windows[1]
        self.app._monitors.monitors = [self.a]
        SYNC(self.app)
        GLIB.drain()
        self.assertTrue(previous.closing)
        self.assertEqual(previous.started, [])
        self.assertEqual(len(self.app.windows), 1)
        self.assertEqual(len(self.app.windows[0].started), 1)

    def test_hotplug_start_does_not_relaunch_running_display(self):
        self.app._monitors.monitors = [self.a]
        SYNC(self.app)
        GLIB.drain()
        prior = self.app.windows[0]
        self.app._monitors.monitors = [self.a, self.b]
        SYNC(self.app)
        self.assertEqual(len(GLIB.queue), 1)
        GLIB.drain()
        self.assertEqual(len(prior.started), 1)
        self.assertEqual(self.app.windows[1].started[0][1], 0)

    def test_hotplug_timer_cannot_restart_after_round_advance(self):
        SYNC(self.app)
        self.app.shared_round = 1
        self.app._monitors.monitors = [self.a]
        SYNC(self.app)
        GLIB.drain()
        self.assertEqual([w.started for w in self.app.windows], [[]])
        START(self.app, tuple(self.app.windows), 1)
        self.assertEqual(len(self.app.windows[0].started), 1)

    def test_shutdown_cancels_all_queued_cohorts(self):
        SYNC(self.app)
        self.app.stopping = True
        GLIB.drain()
        self.assertFalse(any(w.started for w in self.app.windows))

    def test_windowed_preview_keeps_its_own_start_timer(self):
        cls = next(x for x in ast.parse(SOURCE).body if isinstance(x, ast.ClassDef)
                   and x.name == "SaverWindow")
        init = next(x for x in cls.body if isinstance(x, ast.FunctionDef)
                    and x.name == "__init__")
        text = ast.get_source_segment(SOURCE, init)
        self.assertIn("if not defer_start:", text)
        self.assertIn("GLib.timeout_add(350, self._start)", text)


if __name__ == "__main__":
    unittest.main()
