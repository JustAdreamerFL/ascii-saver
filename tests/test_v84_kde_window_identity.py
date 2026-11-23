"""V84: source-level KDE taskbar identity and in-process editor lifecycle.

These checks do not assert that KWin has grouped the real Wayland windows.
"""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def source_method(filename, owner, name):
    tree = ast.parse(read_source(filename))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == owner)
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    scope = {}
    exec(compile(module, filename, 'exec'), scope)
    return scope[name]


class DummyEditor:
    created = []

    def __init__(self, app):
        self.app = app
        self.handlers = {}
        self.present_count = 0
        self.created.append(self)

    def connect(self, name, callback):
        self.handlers[name] = callback

    def present(self):
        self.present_count += 1


class WindowIdentityTests(unittest.TestCase):
    def test_library_is_transient_to_preferences_without_separate_taskbar_slot(self):
        source = (SRC / 'preferences_gallery_view.py').read_text()
        self.assertIn('self.gallery_window = Adw.Window(', source)
        self.assertIn('transient_for=self, title="ASCII Saver · Effect library"', source)
        self.assertIn('transient_for=self', source[source.index('self.gallery_window ='):source.index('self.gallery_window.set_default_size')])
        self.assertIn('self.gallery_window.hide()', (SRC / 'preferences_gallery.py').read_text())

    def test_playlist_editor_uses_main_application_id_and_no_process_spawn(self):
        action = (SRC / 'preferences_actions.py').read_text()
        self.assertIn('self.get_application().open_playlist_editor()', action)
        fn = source_method('preferences_actions.py', 'PreferenceActionsMixin', '_open_playlist_editor')
        app = types.SimpleNamespace(open_playlist_editor=Mock())
        fn(types.SimpleNamespace(get_application=lambda: app), None)
        app.open_playlist_editor.assert_called_once_with()
        source = (SRC / 'playlist_editor.py').read_text()
        self.assertIn("from settings import SettingsApplication", source)
        self.assertIn("'--playlist-editor'", source)
        self.assertNotIn('AsciiSaver.Playlists', source)
        self.assertIn('class Editor(Adw.ApplicationWindow)', source)
        settings = (SRC / 'settings.py').read_text()
        self.assertIn('application_id=APP_ID', settings)
        self.assertIn('com.github.justadreamerfl.asciisaver', settings)
        self.assertIn('com.github.justadreamerfl.asciisaver.desktop', (ROOT / 'install.sh').read_text())

    def test_open_editor_reuses_one_window_and_no_unsolicited_preferences_reload(self):
        DummyEditor.created.clear()
        fn = source_method('application_actions.py', 'ApplicationActionsMixin', 'open_playlist_editor')
        prefs = types.SimpleNamespace(_reload_external_playlists=Mock())
        app = types.SimpleNamespace(playlist_window=None, preferences_window=prefs,
                                    _playlist_editor_closed=Mock())
        with patch.dict(sys.modules, {'playlist_editor': types.SimpleNamespace(Editor=DummyEditor)}):
            fn(app)
            fn(app)
        self.assertEqual(len(DummyEditor.created), 1)
        self.assertIs(DummyEditor.created[0].app, app)
        self.assertEqual(app.playlist_window.present_count, 2)
        self.assertEqual(app.playlist_window.handlers['close-request'], app._playlist_editor_closed)
        prefs._reload_external_playlists.assert_not_called()

    def test_close_reloads_only_saved_playlists_if_preferences_open(self):
        fn = source_method('application_actions.py', 'ApplicationActionsMixin', '_playlist_editor_closed')
        prefs = types.SimpleNamespace(_reload_external_playlists=Mock())
        app = types.SimpleNamespace(playlist_window=object(), preferences_window=prefs)
        self.assertIs(fn(app), False)
        self.assertIsNone(app.playlist_window)
        prefs._reload_external_playlists.assert_called_once_with()
        app.preferences_window = None
        app.playlist_window = object()
        self.assertIs(fn(app), False)
        self.assertIsNone(app.playlist_window)
        prefs._reload_external_playlists.assert_called_once_with()

    def test_editor_closing_releases_preview_pty_and_thumbnail_timers(self):
        fn = source_method('playlist_editor.py', 'Editor', '_editor_closing')
        active = types.SimpleNamespace(close=Mock())
        previews = [types.SimpleNamespace(release=Mock()) for _ in range(3)]
        editor = types.SimpleNamespace(_closed=False, live_preview_window=active,
                                       preview_entries=[(object(), p) for p in previews])
        self.assertIs(fn(editor), False)
        self.assertTrue(editor._closed)
        self.assertIsNone(editor.live_preview_window)
        active.close.assert_called_once_with()
        self.assertEqual(editor.preview_entries, [])
        for preview in previews:
            preview.release.assert_called_once_with()
        editor.live_preview_window = None
        self.assertIs(fn(editor), False)

    def test_stale_queued_thumbnail_refresh_is_ignored_after_close(self):
        fn = source_method('playlist_editor.py', 'Editor', '_sync_effect_previews')
        fn.__globals__['GLib'] = types.SimpleNamespace(SOURCE_REMOVE=False)
        # The early return must happen before any GTK APIs are touched.
        self.assertIs(fn(types.SimpleNamespace(_closed=True)), False)

    def test_version_is_dated_and_explicitly_unverified(self):
        self.assertGreaterEqual(tuple(map(int, (ROOT / 'VERSION').read_text().strip().split('.'))), (0, 84, 0))
        notes = (ROOT / 'docs/releases/RELEASE-V84.md').read_text()
        self.assertIn('KDE Wayland', notes)
        self.assertIn('not verified', notes)
        self.assertIn('## 0.84.0 (experimental) - 2026-11-07', (ROOT / 'CHANGELOG.md').read_text())


if __name__ == '__main__':
    unittest.main()
