"""V73: preserve final effect frames in both library preview modes.

GTK-free contract checks plus execution of the real fullscreen child-exit
callback. Live compositor/VTE verification remains a separate manual step.
"""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
from io import StringIO
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source_for(name: str) -> str:
    return read_source(name)


def preview_spawn_arguments(filename: str) -> list[str]:
    """Inspect the literal argv for the actual VTE spawn, not a documentation string."""
    source = ast.parse(source_for(filename))
    calls = [node for node in ast.walk(source)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
             and node.func.attr == "spawn_async"]
    assert len(calls) == 1
    argv = next(kw.value for kw in calls[0].keywords if kw.arg == "argv")
    assert isinstance(argv, ast.List)
    return [entry.value for entry in argv.elts if isinstance(entry, ast.Constant)
            and isinstance(entry.value, str)]


class PreviewFinalFrameTests(unittest.TestCase):
    def test_both_library_preview_modes_leave_cursor_hidden_and_no_trailing_newline(self):
        for filename in ("effect_preview_window.py", "preferences_gallery.py"):
            with self.subTest(filename=filename):
                args = preview_spawn_arguments(filename)
                for flag in ("--no-eol", "--no-restore-cursor"):
                    self.assertIn(flag, args)
                self.assertIn('terminal.feed(b"\\x1b[?25l")', source_for(filename))

    def test_inline_preview_hides_cursor_both_before_and_after_child(self):
        source = source_for("preferences_gallery.py")
        self.assertLess(source.index('terminal.feed(b"\\x1b[?25l")'),
                        source.index('self.preview_area.set_child(host)'))
        self.assertIn('terminal.feed(b"\\x1b[?25l")\n                    self.preview_title.set_text(f"Finished:', source)

    def test_no_post_exit_screen_clear_or_redraw_in_live_previews(self):
        source = source_for("effect_preview_window.py")
        begin = source.index('            def exited(')
        end = source.index('            terminal.connect(', begin)
        self.assertNotIn('\\x1b[2J', source[begin:end])
        source = source_for("preferences_gallery.py")
        begin = source.index('            def on_exited(')
        end = source.index('            def spawned(', begin)
        self.assertNotIn('\\x1b[2J', source[begin:end])

    def test_gtk_free_rust_contract_no_eol_suppresses_exit_linefeed(self):
        terminal = source_for("ttfx-rust/src/engine/terminal.rs")
        self.assertIn('let end_symbol = if self.config.no_eol { "" } else { end_symbol };', terminal)
        self.assertIn('if !self.config.no_restore_cursor {', terminal)


class FullscreenExitCleanupTests(unittest.TestCase):
    def test_failed_stats_cleanup_cannot_block_monitor_barrier(self):
        source = source_for("app.py")
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef)
                   and n.name == "SaverWindow")
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                      and n.name == "_on_child_exited")
        ast.fix_missing_locations(method)
        scope = dict(time=time, sys=sys, tte_exit_ok=lambda _: True,
                     parse_frame_report=lambda report, expected_effect: {"frames": 1})
        exec(compile(ast.Module(body=[method], type_ignores=[]), "app.py", "exec"), scope)
        stats_file = Mock()
        stats_file.read_text.return_value = '{}'
        stats_file.unlink.side_effect = PermissionError('mock stats file cannot be deleted')
        perf_log = Mock()
        app = SimpleNamespace(perf_log=perf_log, once=False, stopping=False,
                              monitor_effect_finished=Mock())
        terminal = Mock()
        window = SimpleNamespace(terminal=terminal, app=app,
                                 current_stats_path=stats_file,
                                 effect_label='waves', monitor_id='DP-1', effect_started=None,
                                 child_pid=123, running=True, closing=False,
                                 windowed=False, tte_failures=0)
        with redirect_stderr(StringIO()):
            scope['_on_child_exited'](window, terminal, 0)
        self.assertIsNone(window.current_stats_path)
        self.assertIsNone(window.child_pid)
        self.assertFalse(window.running)
        app.monitor_effect_finished.assert_called_once_with(window)
        terminal.feed.assert_called_once_with(b'\x1b[?25l')
        stats_file.unlink.assert_called_once_with(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
