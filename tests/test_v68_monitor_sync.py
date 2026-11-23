"""Headless checks for the per-monitor hold barrier and playlist advancement."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = (Path(__file__).resolve().parents[1] / "src" / "app.py").read_text(encoding="utf-8")


def extracted(name):
    app = next(n for n in ast.parse(SOURCE).body if isinstance(n, ast.ClassDef)
               and n.name == "SaverApplication")
    method = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, "app.py", "exec"), namespace)
    return namespace[name]


class FakeGLib:
    SOURCE_REMOVE = False

    def __init__(self):
        self.timers = []

    def timeout_add(self, delay, callback, *args):
        self.timers.append((delay, callback, args))
        return len(self.timers)

    def drain(self):
        timers, self.timers = self.timers, []
        for _, cb, args in timers:
            cb(*args)


class FakeWindow:
    def __init__(self):
        self.closing = False
        self.started = 0

    def _start(self):
        self.started += 1


class FakeApp:
    def __init__(self, windows, playlist=True):
        self.windows = windows
        self.stopping = False
        self.config = {"effect_hold_seconds": 2, "playlist_mode": playlist}
        self.shared_round = 0
        self.shared_pending = set()
        self.shared_finished = set()
        self.scheduler_calls = 0
        self.playlist_scheduler = SimpleNamespace(next=self.next_effect)
        self.current_playlist_effect = "rain"
        self._advance_when_all_ready = lambda: ADVANCE(self)
        self._start_monitors_for_round = lambda wins, tick: START_COHORT(self, wins, tick)

    def next_effect(self):
        self.scheduler_calls += 1
        return "waves"

    def _overlay_windows(self):
        return self.windows


GLIB = FakeGLib()
ADVANCE = extracted("_advance_when_all_ready")
START_COHORT = extracted("_start_monitors_for_round")
ADVANCE.__globals__["GLib"] = GLIB
ADVANCE.__globals__["TTE_SUCCESS_RESTART_MS"] = 80
START_COHORT.__globals__["GLib"] = GLIB
FINISH = extracted("monitor_effect_finished")
FINISH.__globals__["GLib"] = GLIB
READY = extracted("_monitor_ready")
READY.__globals__["GLib"] = GLIB


class MultiMonitorBarrierTests(unittest.TestCase):
    def setUp(self):
        GLIB.timers.clear()
        self.a, self.b = FakeWindow(), FakeWindow()
        self.app = FakeApp([self.a, self.b])
        self.app._monitor_ready = lambda win, round_no: READY(self.app, win, round_no)

    def test_round_does_not_advance_until_both_effects_and_holds_complete(self):
        FINISH(self.app, self.a)
        self.assertEqual(self.app.shared_round, 0)
        self.assertEqual(len(GLIB.timers), 1)
        GLIB.drain()
        self.assertEqual(self.app.shared_round, 0)
        self.assertEqual((self.a.started, self.b.started), (0, 0))
        FINISH(self.app, self.b)
        GLIB.drain()
        self.assertEqual(self.app.shared_round, 1)
        self.assertEqual(self.app.scheduler_calls, 1)
        self.assertEqual(self.app.current_playlist_effect, "waves")
        # V104: synchronized monitors share ONE next-round start callback.
        self.assertEqual(len(GLIB.timers), 1)
        GLIB.drain()
        self.assertEqual((self.a.started, self.b.started), (1, 1))

    def test_duplicate_completion_only_schedules_one_hold(self):
        FINISH(self.app, self.a)
        FINISH(self.app, self.a)
        self.assertEqual(len(GLIB.timers), 1)

    def test_stale_hold_after_hotplug_or_new_round_cannot_advance(self):
        FINISH(self.app, self.a)
        self.app.shared_round = 1
        GLIB.drain()
        self.assertEqual(self.app.scheduler_calls, 0)
        self.assertEqual(self.app.shared_finished, set())

    def test_closing_disconnected_monitor_is_not_required_for_next_round(self):
        self.app.windows.remove(self.b)
        FINISH(self.app, self.a)
        GLIB.drain()
        self.assertEqual(self.app.shared_round, 1)
        self.assertEqual(self.app.scheduler_calls, 1)

    def test_unordered_mode_advances_barrier_without_touching_playlists(self):
        self.app.config["playlist_mode"] = False
        FINISH(self.app, self.a)
        FINISH(self.app, self.b)
        GLIB.drain()
        self.assertEqual(self.app.shared_round, 1)
        self.assertEqual(self.app.scheduler_calls, 0)


if __name__ == "__main__":
    unittest.main()
