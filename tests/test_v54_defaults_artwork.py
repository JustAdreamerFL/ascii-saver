"""Headless regression checks for Round 2 UI and artwork-library requests."""
from _bootstrap import SRC, read_source  # noqa: F401
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from helpers import load_config
from artwork_library import import_artwork_file, valid_artwork_reference
from artwork_fit import choose_font_sizes
from preferences_defaults import default_for, is_factory_default
from measurements_ui import group_measurements, display_name
from preferences_model import validate_form

ROOT = Path(__file__).resolve().parent.parent

class RoundTwoTests(unittest.TestCase):
    def test_slider_factory_defaults_are_saved_config_independent(self):
        for key in ('speed', 'duration_factor', 'time_scale', 'simulation_hold'):
            self.assertEqual(default_for(key), 1.0)
        self.assertEqual(default_for('frame_rate'), 60.0)
        self.assertEqual(default_for('effect_hold'), 3.0)
        self.assertTrue(is_factory_default(1.0, default_for('speed')))
        self.assertFalse(is_factory_default(1.3, default_for('speed')))

    def test_per_monitor_fit_and_explicit_opt_out(self):
        viewports = {'wide': (180, 55), 'portrait': (75, 80)}
        art = (100, 25)
        self.assertEqual(choose_font_sizes(18, art, viewports, auto_fit=False,
                                           independent=True), {'wide':18, 'portrait':18})
        independently = choose_font_sizes(18, art, viewports,
                                           auto_fit=True, independent=True)
        self.assertEqual(independently['wide'],18)
        self.assertLess(independently['portrait'],18)
        together = choose_font_sizes(18, art, viewports,
                                     auto_fit=True, independent=False)
        self.assertEqual(together['wide'], together['portrait'])
        self.assertEqual(together['portrait'], independently['portrait'])

    def test_artwork_import_preserves_files_and_respects_config(self):
        with TemporaryDirectory() as td:
            base = Path(td)
            user_file = base / 'external' / 'logo.txt'
            user_file.parent.mkdir()
            user_file.write_text('abc\n', encoding='utf-8')
            config = base / 'config'
            path = import_artwork_file(user_file, config)
            self.assertEqual(path, 'artworks/logo.txt')
            self.assertEqual((config/path).read_text(), 'abc\n')
            self.assertEqual(import_artwork_file(config/path, config), path)
            path2 = import_artwork_file(user_file, config)
            self.assertEqual(path2, 'artworks/logo-2.txt')
            self.assertEqual((config/path).read_text(), 'abc\n')
            for bad in ('../logo.txt', '/tmp/a.txt', 'foo/a.txt', '.hidden.txt', 'file.txt/..'):
                self.assertFalse(valid_artwork_reference(bad))
            self.assertTrue(valid_artwork_reference(path))
            saved = {'monitor_artwork':{'DP-1':path}}
            import json
            (config/'config.json').write_text(json.dumps(saved))
            self.assertEqual(load_config(config/'config.json')['monitor_artwork']['DP-1'], path)
            form = validate_form(playlist_json='[]',playlist_enabled=False,font='Monospace 18',
                                 background='#000000',excluded_effects=[],
                                 monitor_artwork={'DP-1':path})
            self.assertEqual(form.monitor_artwork['DP-1'],path)

    def test_adwaita_measurement_groups_are_separate(self):
        rows = [{'monitor':'DP-2','effect':'matrix'}, {'monitor':'DP-1','effect':'beams'},
                {'monitor':'preview','effect':'rain'}]
        groups = group_measurements(rows)
        self.assertEqual(list(groups), ['DP-1','DP-2','preview'])
        self.assertEqual(display_name('preview', {}),'Preview')
        self.assertEqual(display_name('DP-2',{'DP-2':'Portrait monitor'}),'Portrait monitor (DP-2)')

    def test_ui_presents_defaults_separate_json_editor_and_small_window_navigation(self):
        controls = (SRC / 'preferences_controls.py').read_text()
        pages = (SRC / 'preferences_pages.py').read_text()
        shell = (SRC / 'preferences_shell.py').read_text()
        self.assertIn('slider.set_value_pos(Gtk.PositionType.RIGHT)', controls)
        self.assertIn('install_numeric_reset(nested', pages)
        self.assertIn('install_numeric_reset(row', pages)
        self.assertIn('def _open_raw_playlist_editor', pages)
        self.assertNotIn('playlist_frame = Adw.ExpanderRow(', pages)
        self.assertIn('header.set_title_widget(title_box)', shell)
        self.assertIn('self.compact_categories = Gtk.DropDown', shell)
        self.assertNotIn('header.pack_end(self.save_button)', shell)

    def test_new_modules_are_bundled(self):
        installer = (ROOT/'install.sh').read_text()
        for name in ('preferences_defaults', 'artwork_library', 'measurements_ui'):
            self.assertIn(name, installer)
        self.assertIn('self.set_title("ASCII Saver · Preview")', (SRC / 'app.py').read_text())

if __name__ == '__main__': unittest.main()
