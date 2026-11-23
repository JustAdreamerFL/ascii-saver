"""V109: opt-out palette RGB, adaptive navigation, usable drawing modes and close keys.

Pure-model behavior executes headlessly; GTK widget wiring is source-contract
coverage until a real Fedora GNOME/KDE session is available.
"""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401
import ast
import json
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
from helpers import new_config, load_config
from palette_engine import effect_color_arguments
from window_shortcuts import install_close_shortcuts
from test_v70_palette_rounds import RendererPaletteIntegrationTests


def source(name):
    return read_source(name)


class EffectRgbModeTests(unittest.TestCase):
    def test_new_config_keeps_existing_override_default(self):
        self.assertTrue(new_config()['override_effect_colors'])
        self.assertEqual(effect_color_arguments(new_config()), ('--no-color',))

    def test_disabled_override_preserves_ttfx_colors(self):
        cfg = new_config()
        cfg['override_effect_colors'] = False
        self.assertEqual(effect_color_arguments(cfg), ())
        self.assertEqual(effect_color_arguments({'override_effect_colors': 0}), ())

    def test_saved_false_and_true_round_trip_in_loader(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / 'config.json'
            for value in (True, False):
                p.write_text(json.dumps({'override_effect_colors': value}), encoding='utf-8')
                self.assertIs(load_config(p)['override_effect_colors'], value)

    def test_invalid_value_does_not_steal_default(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / 'config.json'
            for value in ('false', None, 0, 1, [], {}):
                p.write_text(json.dumps({'override_effect_colors': value}), encoding='utf-8')
                self.assertTrue(load_config(p)['override_effect_colors'])

    def test_real_fullscreen_argv_respects_toggle(self):
        method = RendererPaletteIntegrationTests.argv_method()
        for enabled in (False, True):
            cfg = new_config()
            cfg['override_effect_colors'] = enabled
            host, _ = RendererPaletteIntegrationTests.window(
                cfg, windowed=False, monitor_id='DP-1')
            argv = method(host)
            self.assertEqual('--no-color' in argv, enabled)
            self.assertIn('--no-restore-cursor', argv)

    def test_preview_argv_respects_toggle(self):
        method = RendererPaletteIntegrationTests.argv_method()
        cfg = new_config()
        cfg['override_effect_colors'] = False
        host, _ = RendererPaletteIntegrationTests.window(
            cfg, windowed=True, monitor_id='default')
        self.assertNotIn('--no-color', method(host))

    def test_both_effect_library_preview_paths_use_the_same_model(self):
        for filename in ('preferences_gallery.py', 'effect_preview_window.py'):
            with self.subTest(filename=filename):
                text = source(filename)
                self.assertIn('effect_color_arguments(', text)
                self.assertNotIn('"--no-color", "--no-eol"', text)
                self.assertNotIn("'--no-color', '--no-eol'", text)

    def test_preferences_toggle_is_saved_and_shown(self):
        for filename, token in (
            ('preferences_controls.py', 'self.override_effect_colors = Adw.SwitchRow()'),
            ('preferences_pages.py', '"Override effect RGB colors"'),
            ('preferences_state.py', '"override_effect_colors": self.override_effect_colors.get_active()'),
        ):
            self.assertIn(token, source(filename))


class ShortcutTests(unittest.TestCase):
    def test_close_shortcuts_capture_before_focused_text_widgets(self):
        events = []
        class Controller:
            def __init__(self): self.callbacks = {}
            def set_propagation_phase(self, phase): events.append(('phase', phase))
            def connect(self, event, callback): self.callbacks[event] = callback
        controller = Controller()
        fake_gtk = SimpleNamespace(
            EventControllerKey=lambda: controller,
            PropagationPhase=SimpleNamespace(CAPTURE='capture'))
        fake_gdk = SimpleNamespace(
            ModifierType=SimpleNamespace(CONTROL_MASK=4), keyval_name=lambda x:x)
        window = SimpleNamespace(close=lambda: events.append('closed'),
                                 add_controller=lambda c: events.append(('controller', c)))
        install_close_shortcuts(window, fake_gtk, fake_gdk)
        self.assertEqual(events[0], ('phase', 'capture'))
        for key, modifiers in [('Escape', 0), ('w', 4), ('q', 4)]:
            self.assertTrue(controller.callbacks['key-pressed'](None, key, None, modifiers))
        self.assertEqual(events.count('closed'), 3)
        self.assertFalse(controller.callbacks['key-pressed'](None, 'x', None, 0))

    def test_all_requested_windows_install_close_shortcuts(self):
        self.assertIn('install_close_shortcuts(self, Gtk, Gdk)', source('settings.py'))
        self.assertIn('install_close_shortcuts(self, Gtk, Gdk)', source('playlist_editor.py'))
        self.assertIn('install_close_shortcuts(self, Gtk, Gdk)', source('artwork_editor.py'))


class ResponsivePreferencesTests(unittest.TestCase):
    def test_compact_and_wide_navigation_are_mutually_exclusive(self):
        shell = source('preferences_shell.py')
        self.assertIn('Gtk.DropDown.new_from_strings', shell)
        self.assertIn('self.navigation_list = Gtk.ListBox()', shell)
        self.assertIn('min-width: 900sp', shell)
        self.assertIn('wide.add_setter(self.wide_sidebar, "visible", True)', shell)
        self.assertIn('wide.add_setter(self.compact_categories, "visible", False)', shell)
        self.assertIn('self.nav_layout.append(self.sections)', shell)
        self.assertIn('self.navigation_list.select_row(self.navigation_rows[names.index(selected)])', shell)

    def test_sliders_are_full_row_and_have_readable_value(self):
        ui = source('adwaita_ui.py')
        controls = source('preferences_controls.py')
        shell = source('preferences_shell.py')
        self.assertIn('self.suffix_box.set_halign(Gtk.Align.FILL)', ui)
        self.assertIn('self.suffix_box.set_hexpand(True)', ui)
        self.assertIn('slider.set_value_pos(Gtk.PositionType.RIGHT)', controls)
        self.assertIn('slider.set_size_request(180, -1)', controls)
        self.assertNotIn('wide.add_setter(row.layout, "orientation", Gtk.Orientation.HORIZONTAL)', shell)

    def test_tools_reside_in_preferences_not_primary_menu(self):
        pages, menu = source('preferences_pages.py'), source('app_menu.py')
        self.assertIn('("tools", "Tools",', source('preferences_shell.py'))
        for item in ('self._open_gallery', 'self._open_playlist_editor',
                     'self._edit_default_artwork', 'self._open_performance',
                     'self._open_duration_profiles', 'self._open_diagnostics'):
            self.assertIn(item, pages)
        self.assertNotIn("menu.append_section('Tools'", menu)

    def test_inline_preview_centers_terminal_vertically(self):
        view = source('preferences_gallery_view.py')
        logic = source('preferences_gallery.py')
        self.assertIn('self.preview_area.set_valign(Gtk.Align.CENTER)', view)
        self.assertIn('host.set_valign(Gtk.Align.CENTER)', logic)
        self.assertIn('host = Gtk.CenterBox(hexpand=True, vexpand=True)', logic)
        self.assertIn('self.preview_area.set_max_content_height(280)', view)

    def test_artwork_editor_exposes_both_modes(self):
        editor = source('artwork_editor.py')
        canvas = source('artwork_canvas_view.py')
        self.assertIn('self.text_mode = Gtk.ToggleButton(label="Text")', editor)
        self.assertIn('self.text_mode.set_group(self.draw_mode)', editor)
        self.assertIn('self.draw_mode.set_active(True)', editor)
        self.assertIn("self.editor_pages.set_visible_child_name(\"canvas\")", editor)
        self.assertIn("drag.connect('drag-update', self._drag_update)", canvas)
        self.assertIn("click.connect('released', self._click_released)", canvas)

    def test_sources_parse_without_gtk_runtime(self):
        for file in ('preferences_shell.py', 'preferences_pages.py',
                     'preferences_state.py', 'preferences_gallery.py',
                     'preferences_gallery_view.py', 'artwork_editor.py',
                     'window_shortcuts.py', 'app.py', 'playlist_editor.py'):
            with self.subTest(file=file): ast.parse(source(file))


if __name__ == '__main__':
    unittest.main()
