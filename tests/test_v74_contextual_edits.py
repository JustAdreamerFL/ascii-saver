"""V74: real callback logic without a GTK/Wayland runtime."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
import json
import types
import unittest
from pathlib import Path
from unittest.mock import Mock

from edit_state import EditBaseline, merge_saved_fields

ROOT = Path(__file__).resolve().parents[1]


def method_from_source(filename, class_name, method, env):
    """Execute a class method's real Python body without importing GTK."""
    tree = ast.parse(read_source(filename))
    owner = next(item for item in tree.body if isinstance(item, ast.ClassDef)
                 and item.name == class_name)
    node = next(item for item in owner.body if isinstance(item, ast.FunctionDef)
                and item.name == method)
    # Type annotations (like Gtk.Button) refer to unavailable UI modules.
    node = ast.FunctionDef(name=node.name, args=node.args, body=node.body,
                           decorator_list=[], returns=None, type_comment=None)
    node.args.args = [ast.arg(arg=arg.arg) for arg in node.args.args]
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    scope = dict(env)
    exec(compile(module, filename, "exec"), scope)
    return scope[method]


class EditStateTests(unittest.TestCase):
    def test_deep_copy_rollback_and_commit(self):
        initial = [{"name": "A", "effects": ["rain"]}]
        state = EditBaseline(initial)
        initial[0]["effects"].append("waves")
        self.assertTrue(state.changed(initial))
        restored = state.restore()
        self.assertEqual(restored, [{"name": "A", "effects": ["rain"]}])
        restored[0]["effects"].append("matrix")
        self.assertEqual(state.restore()[0]["effects"], ["rain"])
        state.commit(initial)
        self.assertFalse(state.changed(initial))
        initial[0]["name"] = "Changed again"
        self.assertTrue(state.changed(initial))

    def test_partial_save_never_marks_unrelated_fields_saved(self):
        original = tuple(f"saved-{i}" for i in range(11))
        current = tuple(f"edited-{i}" for i in range(11))
        actual = merge_saved_fields(original, current, (4, 6))
        self.assertEqual(actual[4], current[4])
        self.assertEqual(actual[6], current[6])
        self.assertTrue(all(actual[i] == original[i] for i in range(11)
                            if i not in (4, 6)))
        with self.assertRaises(ValueError):
            merge_saved_fields(original, current[:-1], (4,))
        with self.assertRaises(ValueError):
            merge_saved_fields(original, current, (11,))

    def test_library_save_writes_only_library_fields_and_keeps_other_dirt(self):
        writes = []
        fn = method_from_source("preferences_gallery.py", "GalleryControllerMixin",
                                "_save_library_changes", {
            "ctl": types.SimpleNamespace(update_config_values=writes.append),
            "merge_saved_fields": merge_saved_fields,
            "Adw": types.SimpleNamespace(Toast=types.SimpleNamespace(new=lambda x: x)),
        })
        original = tuple(f"saved-{i}" for i in range(11))
        current = tuple(f"edited-{i}" for i in range(11))
        dummy = types.SimpleNamespace(
            _saved_snapshot=original,
            _library_baseline=EditBaseline((("matrix",), "inline")),
            _library_snapshot=lambda: (("waves", "rain"), "window"),
            _preference_snapshot=lambda: current,
            _mark_dirty=Mock(), _mark_library_dirty=Mock(),
            library_toast_overlay=types.SimpleNamespace(add_toast=Mock()),
        )
        fn(dummy)
        self.assertEqual(writes, [{"exclude_effects": ["waves", "rain"],
                                   "effect_preview_mode": "window"}])
        self.assertFalse(dummy._library_baseline.changed((("waves", "rain"), "window")))
        self.assertEqual(dummy._saved_snapshot[0], original[0])
        self.assertEqual(dummy._saved_snapshot[4], current[4])
        self.assertEqual(dummy._saved_snapshot[6], current[6])
        self.assertEqual(dummy._saved_snapshot[10], original[10])
        dummy._mark_dirty.assert_called_once()

    def test_library_failed_save_does_not_advance_baseline(self):
        def fail(_changes):
            raise OSError("disk full")
        fn = method_from_source("preferences_gallery.py", "GalleryControllerMixin",
                                "_save_library_changes", {
            "ctl": types.SimpleNamespace(update_config_values=fail),
            "merge_saved_fields": merge_saved_fields,
            "Adw": types.SimpleNamespace(Toast=types.SimpleNamespace(new=lambda x: x)),
        })
        original = tuple(range(11))
        dummy = types.SimpleNamespace(
            _saved_snapshot=original,
            _library_baseline=EditBaseline((("matrix",), "inline")),
            _library_snapshot=lambda: (("waves",), "window"),
            _mark_dirty=Mock(),
            library_toast_overlay=types.SimpleNamespace(add_toast=Mock()),
        )
        fn(dummy)
        self.assertEqual(dummy._saved_snapshot, original)
        self.assertTrue(dummy._library_baseline.changed((("waves",), "window")))
        dummy._mark_dirty.assert_not_called()

    def test_playlist_editor_closed_does_not_reload_other_preferences(self):
        code = (SRC / 'preferences_actions.py').read_text()
        self.assertIn('self.get_application().open_playlist_editor()', code)
        self.assertIn('self.preferences_window._reload_external_playlists()', (SRC / 'application_actions.py').read_text())
        self.assertNotIn('GLib.idle_add(self._load_preferences)', code)

    def test_external_playlists_refresh_preserves_unsaved_other_widgets(self):
        old = json.dumps([{"name": "old"}], indent=2)
        new_items = [{"name": "new"}]
        buffer = FakeBuffer(old)
        saved = tuple(list(range(10)) + [old])
        fn = method_from_source("preferences_state.py", "PreferenceStateMixin",
                                "_reload_external_playlists", {
            "ctl": types.SimpleNamespace(config_file=Path('/config')),
            "load_config": lambda _: {"playlists": new_items},
            "DEFAULT_PLAYLISTS": [],
            "json": json,
            "GLib": types.SimpleNamespace(SOURCE_REMOVE=False),
        })
        dummy = types.SimpleNamespace(
            _closed=False, _saved_snapshot=saved,
            playlists_text=types.SimpleNamespace(get_buffer=lambda: buffer),
            _loading_preferences=False, _mark_dirty=Mock(), _set_notice=Mock(),
        )
        self.assertFalse(fn(dummy))
        self.assertEqual(buffer.text, json.dumps(new_items, indent=2))
        self.assertEqual(dummy._saved_snapshot[:10], saved[:10])
        self.assertEqual(dummy._saved_snapshot[-1], buffer.text)
        self.assertFalse(dummy._loading_preferences)
        dummy._set_notice.assert_not_called()

    def test_external_playlists_does_not_erase_unsaved_json(self):
        old = json.dumps([{"name": "old"}], indent=2)
        changed = json.dumps([{"name": "draft"}], indent=2)
        buffer = FakeBuffer(changed)
        fn = method_from_source("preferences_state.py", "PreferenceStateMixin",
                                "_reload_external_playlists", {
            "ctl": types.SimpleNamespace(config_file=Path('/config')),
            "load_config": lambda _: {"playlists": [{"name": "saved elsewhere"}]},
            "DEFAULT_PLAYLISTS": [],
            "json": json,
            "GLib": types.SimpleNamespace(SOURCE_REMOVE=False),
        })
        dummy = types.SimpleNamespace(
            _closed=False, _saved_snapshot=tuple(list(range(10)) + [old]),
            playlists_text=types.SimpleNamespace(get_buffer=lambda: buffer),
            _loading_preferences=False, _mark_dirty=Mock(), _set_notice=Mock(),
        )
        fn(dummy)
        self.assertEqual(buffer.text, changed)
        self.assertIn('saved elsewhere', dummy._saved_snapshot[-1])
        dummy._set_notice.assert_called_once()

    def test_playlist_editor_operations_have_local_dirty_indicators(self):
        source = (SRC / 'playlist_editor.py').read_text()
        tree = ast.parse(source)
        editor = next(item for item in tree.body if isinstance(item, ast.ClassDef)
                      and item.name == 'Editor')
        for name in ('generate_playlists', 'generate_measured_playlists',
                     'modify', 'toggle_effect', 'add', 'remove', 'move', 'save', 'discard'):
            fn = next(item for item in editor.body if isinstance(item, ast.FunctionDef)
                      and item.name == name)
            self.assertIn('self._mark_playlist_dirty()', ast.get_source_segment(source, fn), name)
        self.assertIn('self.unsaved_banner.set_child(banner_row)', source)
        self.assertIn('overlay.add_overlay(self.unsaved_banner)', source)
        self.assertNotIn('content_header.pack_end(save)', source)

    def test_library_has_contextual_buttons_and_installed_state(self):
        source = (SRC / 'preferences_gallery_view.py').read_text()
        self.assertIn('discard_library.connect("clicked", self._discard_library_changes)', source)
        self.assertIn('save_library.connect("clicked", self._save_library_changes)', source)
        self.assertIn('library_overlay.add_overlay(self.library_unsaved_banner)', source)
        installer = (ROOT / 'install.sh').read_text()
        self.assertIn('"$py_src/edit_state.py"', installer)


class FakeBuffer:
    def __init__(self, text):
        self.text = text
    def get_start_iter(self):
        return 0
    def get_end_iter(self):
        return len(self.text)
    def get_text(self, _start, _end, _include_hidden):
        return self.text
    def set_text(self, value):
        self.text = value


if __name__ == '__main__':
    unittest.main()
