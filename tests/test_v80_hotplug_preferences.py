"""Regression tests for Preferences monitor connect/disconnect handling."""
from __future__ import annotations
import ast
from pathlib import Path
import unittest
from monitor_config import extend_monitor_baseline, merge_monitor_settings

ROOT = Path(__file__).resolve().parents[1]


class MonitorConfigTests(unittest.TestCase):
    def setUp(self):
        self.saved = (('saved-global',), (60,), 'font', '#000', 0,
                      ('#FFF',), (),
                      (('DP-1', 60),),
                      (('DP-1', 'logo.txt'),),
                      (('DP-1', ('#111', '#222', '#333')),), 'playlists')

    def test_new_display_is_not_an_unsaved_edit(self):
        current = list(self.saved)
        current[7] = (('DP-1', 60), ('HDMI-1', 144))
        current[8] = (('DP-1', 'logo.txt'), ('HDMI-1', 'artworks/new.txt'))
        current[9] = (('DP-1', ('#111', '#222', '#333')),
                      ('HDMI-1', ('#AAA', '#BBB', '#CCC')))
        self.assertEqual(extend_monitor_baseline(self.saved, tuple(current), {'HDMI-1'}), tuple(current))

    def test_existing_unsaved_changes_still_show_dirty(self):
        current = list(self.saved)
        current[0] = ('unsaved-global',)
        current[7] = (('DP-1', 120), ('HDMI-1', 144))
        current[8] = (('DP-1', 'logo.txt'), ('HDMI-1', ''))
        current[9] = (('DP-1', ('#111', '#222', '#333')),
                      ('HDMI-1', ('#AAA', '#BBB', '#CCC')))
        result = extend_monitor_baseline(self.saved, tuple(current), {'HDMI-1'})
        self.assertNotEqual(result, tuple(current))
        self.assertEqual(result[0], self.saved[0])
        self.assertEqual(dict(result[7])['DP-1'], 60)
        self.assertEqual(dict(result[7])['HDMI-1'], 144)

    def test_disconnect_does_not_remove_existing_baseline(self):
        same = extend_monitor_baseline(self.saved, self.saved, set())
        self.assertEqual(same, self.saved)

    def test_save_merges_unknown_disconnected_displays(self):
        saved = {
            'monitor_fps': {'DP-1': 120, 'HDMI-2': 75},
            'monitor_artwork': {'DP-1': 'old.txt', 'HDMI-2': 'artworks/snow.txt'},
            'monitor_visuals': {
                'DP-1': {'palette': ['#000'], 'extra': 'preserve'},
                'HDMI-2': {'palette': ['#999']},
            },
        }
        result = merge_monitor_settings(
            saved, {'DP-1': 90}, {'DP-1': 'new.txt'}, {'DP-1': ['#123456']})
        self.assertEqual(result['monitor_fps'], {'DP-1': 90, 'HDMI-2': 75})
        self.assertEqual(result['monitor_artwork']['HDMI-2'], 'artworks/snow.txt')
        self.assertEqual(result['monitor_visuals']['HDMI-2']['palette'], ['#999'])
        self.assertEqual(result['monitor_visuals']['DP-1']['palette'], ['#123456'])
        self.assertEqual(result['monitor_visuals']['DP-1']['extra'], 'preserve')
        self.assertEqual(saved['monitor_fps']['DP-1'], 120)
        self.assertEqual(saved['monitor_visuals']['DP-1']['palette'], ['#000'])

    def test_empty_visible_displays_do_not_wipe_maps(self):
        existing = {'monitor_fps': {'DP-1': 60},
                    'monitor_artwork': {'DP-1': ''},
                    'monitor_visuals': {'DP-1': {'palette': ['#FFFFFF']}}}
        self.assertEqual(merge_monitor_settings(existing, {}, {}, {}), existing)


class HotplugSourceTests(unittest.TestCase):
    def test_hotplug_signal_reconciles_rows(self):
        source = (ROOT / 'settings.py').read_text()
        controls = (ROOT / 'preferences_controls.py').read_text()
        self.assertIn('self._sync_monitor_widgets()', source)
        self.assertIn('def _sync_monitor_widgets(self):', controls)
        self.assertIn('self.monitor_rates_group.remove(fps_row)', controls)
        self.assertIn('self.monitor_rates_group.add(fps_row)', controls)
        self.assertIn('self._monitor_connected = set(targets)', controls)
        self.assertIn('self._monitor_rows[connector]', controls)

    def test_new_monitor_controls_get_dirty_signals(self):
        source = (ROOT / 'preferences_controls.py').read_text()
        self.assertIn('spin.connect("value-changed", self._mark_dirty)', source)
        self.assertIn('artwork.connect("changed", self._mark_dirty)', source)
        self.assertIn('button.connect("notify::rgba", self._mark_dirty)', source)
        self.assertIn('extend_monitor_baseline(', source)
        self.assertIn('self._monitor_signals_connected = True',
                      (ROOT / 'preferences_state.py').read_text())

    def test_save_preserves_disconnected_config(self):
        source = (ROOT / 'preferences_state.py').read_text()
        self.assertIn('stored_monitor_settings = merge_monitor_settings(', source)
        self.assertIn('"monitor_fps": stored_monitor_settings["monitor_fps"]', source)
        self.assertIn('"monitor_visuals": stored_monitor_settings["monitor_visuals"]', source)
        self.assertIn('"monitor_artwork": stored_monitor_settings["monitor_artwork"]', source)

    def test_new_helper_installed(self):
        source = (ROOT / 'install.sh').read_text()
        self.assertIn('"$source_dir/monitor_config.py" "$staged_app/monitor_config.py"', source)
        for f in ('settings.py', 'preferences_controls.py', 'preferences_state.py', 'monitor_config.py'):
            ast.parse((ROOT / f).read_text())


if __name__ == '__main__':
    unittest.main()

class HotplugLogicTests(unittest.TestCase):
    """Run the actual GTK-independent reconciliation method with fake rows."""

    def test_attach_detach_reattach_preserves_widgets_and_dirty_state(self):
        # Extract the real method rather than mocking its algorithm. Only the
        # GDK display and PreferencesGroup rows are fake.
        tree = ast.parse((ROOT / 'preferences_controls.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == 'PreferenceControlsMixin')
        fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                  and n.name == '_sync_monitor_widgets')
        unit = ast.Module(body=[fn], type_ignores=[])
        ast.fix_missing_locations(unit)

        class Monitor:
            def __init__(self, connector):
                self.connector = connector
            def get_connector(self):
                return self.connector
            def get_model(self):
                return 'Monitor'

        class Model:
            items = [Monitor('DP-1')]
            def get_n_items(self):
                return len(self.items)
            def get_item(self, i):
                return self.items[i]

        class Display:
            def get_monitors(self):
                return model
        class Gdk:
            class Display:
                @staticmethod
                def get_default():
                    return Display()

        class Row:
            def set_title(self, value):
                self.title = value

        class Group:
            def __init__(self):
                self.children = []
            def add(self, row):
                if row in self.children:
                    raise AssertionError('duplicate row')
                self.children.append(row)
            def remove(self, row):
                self.children.remove(row)

        model = Model()
        namespace = {'Gdk': Gdk, 'load_config': lambda *_args: {},
                     'ctl': type('Ctl', (), {'config_file': None})()}
        exec(compile(unit, 'preferences_controls.py', 'exec'), namespace)

        class Form:
            def __init__(self):
                self._monitor_rows = {}
                self._monitor_connected = set()
                self.monitor_rates_group = Group()
                self.monitor_colors_group = Group()
                self.monitor_labels = {}
                self._loading_preferences = False
                self._saved_snapshot = (
                    ('saved',), (60,), 'font', '#000', 0, ('#FFF',), (),
                    (), (), (), 'playlists')
                self.calls = 0
            def _create_monitor_widgets(self, connector, label, _config):
                rows = (Row(), Row(), Row())
                self._monitor_rows[connector] = rows
                self.monitor_rates_group.add(rows[0])
                self.monitor_colors_group.add(rows[1])
                self.monitor_colors_group.add(rows[2])
            def _preference_snapshot(self):
                pairs = tuple((k, 60) for k in sorted(self._monitor_rows))
                artworks = tuple((k, '') for k in sorted(self._monitor_rows))
                colors = tuple((k, ('#FFF',)) for k in sorted(self._monitor_rows))
                return (('saved',), (60,), 'font', '#000', 0, ('#FFF',), (),
                        pairs, artworks, colors, 'playlists')
            def _mark_dirty(self):
                self.calls += 1
                self.dirty = self._preference_snapshot() != self._saved_snapshot

        form = Form()
        reconcile = namespace['_sync_monitor_widgets']
        reconcile(form)
        self.assertFalse(form.dirty)
        dp_row = form._monitor_rows['DP-1'][0]
        model.items.append(Monitor('HDMI-1'))
        reconcile(form)
        self.assertFalse(form.dirty)
        hdmi_row = form._monitor_rows['HDMI-1'][0]
        self.assertEqual(len(form.monitor_rates_group.children), 2)
        model.items = [model.items[1]]
        reconcile(form)
        self.assertNotIn(dp_row, form.monitor_rates_group.children)
        self.assertFalse(form.dirty)
        model.items.append(Monitor('DP-1'))
        reconcile(form)
        self.assertIs(form._monitor_rows['DP-1'][0], dp_row)
        self.assertIs(form._monitor_rows['HDMI-1'][0], hdmi_row)
        self.assertFalse(form.dirty)
        self.assertEqual(len(form.monitor_rates_group.children), 2)
