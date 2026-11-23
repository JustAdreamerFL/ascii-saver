"""Headless regression tests for V69 monitor font fitting and config isolation."""
from _bootstrap import SRC, read_source  # noqa: F401
from pathlib import Path
import unittest

from artwork_fit import choose_artwork_font_sizes, choose_font_sizes
from helpers import DEFAULT_CONFIG, new_config

ROOT = Path(__file__).resolve().parents[1]


class MonitorFitModes(unittest.TestCase):
    def setUp(self):
        self.grids = {'landscape': (170, 55), 'portrait': (65, 90)}

    def test_independent_monitors_use_different_sizes_for_same_artwork(self):
        result = choose_font_sizes(18, (100, 30), self.grids,
                                   auto_fit=True, independent=True)
        self.assertEqual(result['landscape'], 18)
        self.assertLess(result['portrait'], 18)

    def test_shared_mode_uses_smallest_fit_across_displays(self):
        result = choose_font_sizes(18, (100, 30), self.grids,
                                   auto_fit=True, independent=False)
        self.assertEqual(result['landscape'], result['portrait'])
        self.assertLess(result['landscape'], 18)

    def test_independent_mode_handles_different_user_artwork(self):
        result = choose_artwork_font_sizes(
            18, {'landscape': (160, 30), 'portrait': (40, 30)},
            self.grids, auto_fit=True, independent=True)
        self.assertEqual(result, {'landscape': 18, 'portrait': 18})
        larger = choose_artwork_font_sizes(
            18, {'landscape': (160, 30), 'portrait': (110, 30)},
            self.grids, auto_fit=True, independent=True)
        self.assertLess(larger['portrait'], 18)
        self.assertEqual(larger['landscape'], 18)

    def test_shared_mode_accounts_for_every_artwork(self):
        result = choose_artwork_font_sizes(
            18, {'landscape': (100, 30), 'portrait': (110, 30)},
            self.grids, auto_fit=True, independent=False)
        self.assertEqual(result['landscape'], result['portrait'])
        self.assertLess(result['portrait'], 18)

    def test_turning_off_fit_recovers_saved_font_in_both_modes(self):
        art = {name: (200, 40) for name in self.grids}
        for independent in (False, True):
            with self.subTest(independent=independent):
                enabled = choose_artwork_font_sizes(
                    18, art, self.grids, auto_fit=True,
                    independent=independent)
                self.assertTrue(any(size < 18 for size in enabled.values()))
                disabled = choose_artwork_font_sizes(
                    18, art, self.grids, auto_fit=False,
                    independent=independent)
                self.assertEqual(disabled, {name: 18 for name in self.grids})

    def test_unavailable_artwork_never_forces_font_shrink(self):
        self.assertEqual(choose_artwork_font_sizes(
            18, {'landscape': (0, 0), 'portrait': (0, 0)},
            self.grids, auto_fit=True, independent=False),
            {name: 18 for name in self.grids})

    def test_no_monitors_returns_empty_plan(self):
        self.assertEqual(choose_artwork_font_sizes(
            18, {}, {}, auto_fit=True, independent=False), {})


class ConfigDefaultsIsolation(unittest.TestCase):
    def test_mutable_defaults_are_not_shared_between_loads(self):
        one = new_config()
        one['monitor_fps']['DP-1'] = 30
        one['monitor_artwork']['DP-1'] = 'artworks/large.txt'
        one['palette'][0] = '#FFFFFF'
        one['monitor_visuals']['DP-1'] = {'palette': ['#FFFFFF']}
        one['exclude_effects'].clear()
        two = new_config()
        self.assertEqual(two, DEFAULT_CONFIG)
        self.assertNotIn('DP-1', two['monitor_fps'])
        self.assertNotIn('DP-1', two['monitor_artwork'])
        self.assertNotIn('DP-1', two['monitor_visuals'])


class RuntimeFitWiring(unittest.TestCase):
    def test_renderer_restores_baseline_and_supports_shared_fit(self):
        src = (SRC / 'app.py').read_text()
        start = src.index('    def _auto_fit_monitor_artwork(')
        end = src.index('    def _tte_argv(', start)
        fit = src[start:end]
        self.assertLess(fit.index('self.terminal.set_font(desc)'),
                        fit.index('if not self.app.config.get("auto_fit_artwork", True)'))
        self.assertIn('not independent and self.app._monitors is not None', fit)
        self.assertIn('choose_artwork_font_sizes(', fit)

    def test_shared_fit_control_is_not_hidden_in_independent_section(self):
        ui = (SRC / 'preferences_pages.py').read_text()
        self.assertLess(ui.index('self.section_groups["displays"].add(self.auto_fit_artwork)'),
                        ui.index('self.monitor_revealer = Gtk.Revealer()'))


if __name__ == '__main__':
    unittest.main()
