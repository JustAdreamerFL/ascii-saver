"""V77 regression coverage for the user-observed single-effect preview UX.

GTK introspection isn't available in headless CI. Inspect the *actual spawn*
arguments and GTK lifecycle methods, not release-note prose.
"""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return read_source(name)


def call_args(file_name):
    tree = ast.parse(source(file_name))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'spawn_async']
    assert len(calls) == 1
    argv = next(k.value for k in calls[0].keywords if k.arg == 'argv')
    return [part.value for part in argv.elts if isinstance(part, ast.Constant)]


class PreviewUsabilityTests(unittest.TestCase):
    def test_both_previews_center_artwork_with_native_renderer(self):
        cli = source('ttfx-rust/src/cli.rs')
        engine = source('ttfx-rust/src/engine/terminal.rs')
        self.assertIn('long = "anchor-canvas"', cli)
        self.assertIn('calc_canvas_offsets(config, &canvas, width, height)', engine)
        self.assertIn('S | N | C => column_offset', engine)
        self.assertIn('W | E | C => row_offset', engine)
        for file_name in ('effect_preview_window.py', 'preferences_gallery.py'):
            with self.subTest(file=file_name):
                args = call_args(file_name)
                self.assertEqual('c', args[args.index('--anchor-canvas') + 1])
                self.assertNotIn('--no-color', args)  # palette override now conditional
                self.assertIn('--no-eol', args)

    def test_replay_is_in_preview_and_reuses_latest_effect(self):
        tree = ast.parse(source('effect_preview_window.py'))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == 'EffectPreviewWindow')
        replay = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                      and node.name == '_replay')
        play = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'play')
        replay_source = ast.get_source_segment(source('effect_preview_window.py'), replay)
        play_source = ast.get_source_segment(source('effect_preview_window.py'), play)
        self.assertIn('effect, font_name, palette_config = self._last_play', replay_source)
        self.assertIn('self.play(effect, font_name, palette_config)', replay_source)
        self.assertIn('self._last_play = (effect, font_name, palette_config)', play_source)
        self.assertIn('self.replay_button.set_sensitive(True)', play_source)
        self.assertIn('replay.connect(\'clicked\', self._replay)', source('effect_preview_window.py'))

    def test_no_redundant_close_or_help_in_separate_preview(self):
        view = source('effect_preview_window.py')
        self.assertNotIn("Gtk.Button(label='Close preview')", view)
        self.assertNotIn('Independent preview: mouse movement', view)
        self.assertIn("self.connect('close-request', self._close_requested)", view)
        self.assertIn('header.pack_end(replay)', view)

    def test_effect_library_thumbnail_toggles_selection_without_launching_renderer(self):
        view = source('preferences_gallery_view.py')
        tree = ast.parse(view)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == 'GalleryViewMixin')
        toggle = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                      and node.name == '_toggle_gallery_thumbnail')
        action = ast.get_source_segment(view, toggle)
        self.assertIn('check.set_active(not check.get_active())', action)
        self.assertNotIn('_preview_effect', action)
        self.assertIn('thumbnail_button.set_child(image)', view)
        self.assertIn('thumbnail_button.connect("clicked", self._toggle_gallery_thumbnail, check)', view)
        self.assertIn('button.connect("clicked", self._preview_effect, name)', view)

    def test_pinned_canvas_has_usable_minimum_height_and_library_remains_scrollable(self):
        view = source('preferences_gallery_view.py')
        self.assertIn('self.preview_area.set_min_content_height(240)', view)
        self.assertIn('self.preview_area.set_max_content_height(280)', view)
        self.assertIn('gallery_scroll.set_vexpand(True)', view)
        self.assertIn('gallery_scroll.set_min_content_height(320)', view)
        self.assertIn('gallery_shell.append(self.live_preview_revealer)', view)
        self.assertNotIn('title="Preview window behavior"', view)


if __name__ == '__main__':
    unittest.main()
