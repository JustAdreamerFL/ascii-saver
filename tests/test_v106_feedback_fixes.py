"""V106: real regressions for palette migration and UI identity/layout."""
from __future__ import annotations
import ast
import json
import tempfile
import unittest
from pathlib import Path
from helpers import load_config, new_config
from palette_engine import palette_color_for_round

ROOT = Path(__file__).resolve().parents[1]

class PaletteMigrationTests(unittest.TestCase):
    def test_fresh_install_cycles_instead_of_freezing_first_swatch(self):
        cfg = new_config()
        self.assertTrue(cfg['cycle_palette'])
        self.assertEqual(cfg['palette_mode'], 'cycle')
        self.assertEqual([palette_color_for_round(cfg, None, i) for i in range(4)],
                         ['#F2F2F2', '#94D2BD', '#EE9B00', '#F2F2F2'])

    def test_pre_v106_saved_false_default_gets_migrated(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'config.json'
            target.write_text(json.dumps({'cycle_palette': False, 'palette':
                ['#FF0000','#00FF00','#0000FF']}))
            cfg = load_config(target)
        self.assertTrue(cfg['cycle_palette'])
        self.assertEqual(palette_color_for_round(cfg, None, 1), '#00FF00')

    def test_explicit_static_choice_stays_static(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'config.json'
            target.write_text(json.dumps({'cycle_palette': False, 'palette_mode': 'static',
                                        'palette': ['#FF0000','#00FF00']}))
            cfg = load_config(target)
        self.assertFalse(cfg['cycle_palette'])
        self.assertEqual([palette_color_for_round(cfg,None,i) for i in range(3)],
                         ['#FF0000']*3)

    def test_explicit_mode_takes_precedence_over_old_boolean(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'config.json'
            target.write_text(json.dumps({'palette_mode': 'cycle', 'cycle_palette': False}))
            self.assertTrue(load_config(target)['cycle_palette'])

    def test_invalid_mode_does_not_block_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'config.json'
            target.write_text(json.dumps({'palette_mode': 'unsupported', 'cycle_palette': False}))
            self.assertTrue(load_config(target)['cycle_palette'])

    def test_pingpong_with_new_default(self):
        cfg = new_config()
        cfg['palette_ping_pong']=True
        self.assertEqual(palette_color_for_round(cfg,None,3), cfg['palette'][1])

class GUIStructureTests(unittest.TestCase):
    def test_modal_windows_do_not_pack_second_close_button(self):
        src=(ROOT/'app_menu.py').read_text()
        self.assertIn('Adw.Window(title=title, transient_for=parent, modal=True)',src)
        self.assertIn('Gdk.KEY_Escape',src)
        self.assertNotIn('header.pack_end(close_button)',src)
        self.assertNotIn("Gtk.Button(label='Close'",src)

    def test_preview_desktop_id_and_separate_gapplication_instances(self):
        src=(ROOT/'app.py').read_text()
        settings=(ROOT/'settings.py').read_text()
        self.assertIn('APP_ID = "io.github.robbybobby77.AsciiSaver"',src)
        self.assertIn('APP_ID = "io.github.robbybobby77.AsciiSaver"',settings)
        self.assertIn('flags=Gio.ApplicationFlags.NON_UNIQUE',src)
        self.assertIn('flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE', settings)
        self.assertIn('io.github.robbybobby77.AsciiSaver.desktop', (ROOT/'install.sh').read_text())

    def test_compact_preference_rows_move_controls_below_labels(self):
        src=(ROOT/'preferences_shell.py').read_text()
        ui=(ROOT/'adwaita_ui.py').read_text()
        self.assertIn('class AdaptiveControlRow(Adw.PreferencesRow)', ui)
        self.assertIn('self.set_child(self.layout)',ui)
        # V107 stacks controls by default so a minimum width cannot defeat a breakpoint.
        self.assertIn('self.layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL',ui)
        self.assertNotIn('compact_controls.add_setter(', src)
        self.assertIn('self._adaptive_rows.append(row)',(ROOT/'preferences_pages.py').read_text())

    def test_save_actions_do_not_cover_preference_rows(self):
        src=(ROOT/'preferences_shell.py').read_text()
        self.assertIn('toolbar_view.add_bottom_bar(self.changes_tray)',src)
        self.assertIn('self.changes_tray = self.unsaved_banner',src)
        self.assertNotIn('content_overlay.add_overlay(self.unsaved_banner)',src)
        state=(ROOT/'preferences_state.py').read_text()
        self.assertIn('self.changes_tray.set_reveal_child(is_dirty)',state)
        self.assertIn('self.changes_tray.set_reveal_child(False)',state)

    def test_sources_parse_and_version(self):
        for name in ('app_menu.py','app.py','helpers.py','preferences_shell.py',
                     'preferences_state.py','preferences_pages.py','adwaita_ui.py'):
            ast.parse((ROOT/name).read_text())
        self.assertGreaterEqual(tuple(map(int,(ROOT/'VERSION').read_text().strip().split('.'))), (0,106,0))

if __name__=='__main__':unittest.main()
