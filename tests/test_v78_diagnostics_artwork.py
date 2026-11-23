"""Regression tests for reported Diagnostics / Edit Artwork workflow problems."""
from __future__ import annotations
import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from types import SimpleNamespace

from artwork_editor_io import editor_close_message, read_artwork, save_artwork
from diagnostics_model import diagnostic_report, diagnostic_summary

ROOT = Path(__file__).resolve().parents[1]


def source(name: str) -> str:
    return (ROOT / name).read_text(encoding='utf-8')


class DiagnosticsModelTests(unittest.TestCase):
    def test_grouped_results_keep_pass_fail_and_details(self):
        checks = [('GTK/VTE', True, 'available'), ('watcher', False, 'not running')]
        self.assertEqual(diagnostic_summary(checks), '1 of 2 checks passed.')
        report = diagnostic_report(checks)
        self.assertIn('PASS  GTK/VTE: available', report)
        self.assertIn('FAIL  watcher: not running', report)
        self.assertIn('1 of 2 checks passed.', report)
        self.assertEqual(diagnostic_summary([('check', True, 'ok')]), 'All 1 checks passed.')
        self.assertEqual(diagnostic_summary([]), 'No diagnostic checks returned.')

    def test_doctor_uses_separate_window_not_general_notice(self):
        src = source('preferences_actions.py')
        tree = ast.parse(src)
        self.assertIn('if command == "doctor":\n            self._open_diagnostics(_button)\n            return', src)
        self.assertIn('from diagnostics_view import DiagnosticsWindow', src)
        view = source('diagnostics_view.py')
        ast.parse(view)
        self.assertIn('ctl.collect_diagnostics()', view)
        self.assertIn('threading.Thread(target=worker, daemon=True).start()', view)
        self.assertIn('generation != self._generation', view)
        self.assertIn('Adw.PreferencesGroup(', view)
        for action in ('_run', '_clear', '_copy', '_close_requested'):
            self.assertIn(f'def {action}(', view)
        self.assertIn('get_clipboard().set_text(diagnostic_report(self._checks))', view)
        self.assertIn('diagnostics_model diagnostics_view', source('install.sh'))


class ArtworkCompletionTests(unittest.TestCase):
    def test_close_feedback_depends_on_actual_save_or_discard(self):
        self.assertEqual(editor_close_message(0, False),
                         'Artwork editor closed without changes.')
        self.assertEqual(editor_close_message(0, True),
                         'Unsaved artwork edits discarded.')
        self.assertEqual(editor_close_message(1, False), 'Artwork saved.')
        self.assertEqual(editor_close_message(1, True),
                         'Artwork saved. Later unsaved edits discarded.')

    def test_save_is_real_atomic_file_write_and_failure_leaves_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'logo.txt'
            path.write_text('original', encoding='utf-8')
            save_artwork(path, 'saved\ntext')
            self.assertEqual(read_artwork(path), 'saved\ntext')
            with patch('artwork_editor_io.os.fsync', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    save_artwork(path, 'never saved')
            self.assertEqual(read_artwork(path), 'saved\ntext')
            self.assertEqual(list(Path(directory).glob('.artwork-*')), [])

    def test_close_request_actual_method_never_reports_uncommitted_work(self):
        tree = ast.parse(source('artwork_editor.py'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == 'ArtworkEditor')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                      and n.name == '_close_requested')
        module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
        namespace = {'editor_close_message': editor_close_message}
        exec(compile(module, 'artwork_editor.py', 'exec'), namespace)
        close_requested = namespace['_close_requested']
        finish = Mock()
        prompt = Mock()
        fake = SimpleNamespace(_text=lambda: 'not saved', original_text='original',
                               _close_confirmed=False, _close_dialog_open=False,
                               _confirm_discard=prompt, _reported_close=False,
                               _saved_count=0, _discarded_edits=False,
                               _on_finished=finish)
        self.assertTrue(close_requested(fake))
        prompt.assert_called_once()
        finish.assert_not_called()
        fake._close_confirmed = True
        fake._discarded_edits = True
        self.assertFalse(close_requested(fake))
        finish.assert_called_once_with('Unsaved artwork edits discarded.')
        self.assertFalse(close_requested(fake))
        self.assertEqual(finish.call_count, 1)

    def test_save_callback_does_not_mark_failed_write_as_saved(self):
        tree = ast.parse(source('artwork_editor.py'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == 'ArtworkEditor')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                      and n.name == '_save')
        module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
        toast = Mock()
        adw = SimpleNamespace(Toast=SimpleNamespace(new=lambda msg: msg))
        failing_save = Mock(side_effect=OSError('full disk'))
        namespace = {'save_artwork': failing_save, 'Adw': adw}
        exec(compile(module, 'artwork_editor.py', 'exec'), namespace)
        fake = SimpleNamespace(_text=lambda: 'new text', path=Path('/not/accessed'),
                               toasts=toast, original_text='old', _saved_count=0,
                               _changed=Mock())
        namespace['_save'](fake)
        self.assertEqual(fake._saved_count, 0)
        self.assertEqual(fake.original_text, 'old')
        fake._changed.assert_not_called()
        toast.add_toast.assert_called_once_with('Could not save artwork: full disk')

    def test_unsaved_close_asks_and_only_reports_after_confirmed_close(self):
        editor = source('artwork_editor.py')
        ast.parse(editor)
        self.assertIn('self.connect("close-request", self._close_requested)', editor)
        self.assertIn('if self._text() != self.original_text and not self._close_confirmed:', editor)
        self.assertIn('self._confirm_discard()', editor)
        self.assertIn('if response == "discard":', editor)
        self.assertIn('self._close_confirmed = True', editor)
        self.assertIn('self._saved_count += 1', editor)
        self.assertIn('editor_close_message(self._saved_count, self._discarded_edits)', editor)
        self.assertIn('self._on_finished(message)', editor)
        for name in ('preferences_actions.py', 'preferences_controls.py'):
            self.assertIn('on_finished=finished', source(name))
            self.assertNotIn('editor.connect("close-request",', source(name))


if __name__ == '__main__':
    unittest.main()
