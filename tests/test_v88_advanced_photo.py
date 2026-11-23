"""V88 Artwork Studio advanced controls: pure conversion and UI contracts."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
from dataclasses import replace
from pathlib import Path
import unittest

from photo_ascii import PhotoSettings, RAMPS, photo_to_ascii

ROOT = Path(__file__).resolve().parents[1]


def gray_image(width, height, intensity):
    return bytes(channel for y in range(height) for x in range(width)
                 for channel in (intensity(x, y),) * 3)


class AdvancedConversionTests(unittest.TestCase):
    def setUp(self):
        self.settings = PhotoSettings(columns=32, rows=16)
        self.mid_gray = gray_image(32, 32, lambda _x, _y: 120)

    def test_all_advanced_defaults_preserve_legacy_output(self):
        original = photo_to_ascii(self.mid_gray, 32, 32, settings=self.settings)
        explicit = replace(self.settings, gamma=1.0, edge=0, dither=False)
        self.assertEqual(photo_to_ascii(self.mid_gray, 32, 32, settings=explicit), original)
        self.assertEqual(set(original.replace('\n', '')), {'+'})

    def test_gamma_changes_midtones_not_extremes(self):
        darker = photo_to_ascii(self.mid_gray, 32, 32,
                                settings=replace(self.settings, gamma=0.6))
        normal = photo_to_ascii(self.mid_gray, 32, 32, settings=self.settings)
        brighter = photo_to_ascii(self.mid_gray, 32, 32,
                                  settings=replace(self.settings, gamma=1.8))
        ramp = RAMPS[self.settings.ramp]
        self.assertLess(ramp.index(darker[0]), ramp.index(normal[0]))
        self.assertLess(ramp.index(normal[0]), ramp.index(brighter[0]))
        for intensity in (0, 255):
            pixels = gray_image(32, 32, lambda _x, _y: intensity)
            self.assertEqual(photo_to_ascii(pixels, 32, 32,
                                            settings=replace(self.settings, gamma=0.6)),
                             photo_to_ascii(pixels, 32, 32,
                                            settings=replace(self.settings, gamma=1.8)))

    def test_dithering_uses_multiple_densities_and_is_deterministic(self):
        non_dither = photo_to_ascii(self.mid_gray, 32, 32, settings=self.settings)
        dithered = photo_to_ascii(self.mid_gray, 32, 32,
                                 settings=replace(self.settings, dither=True))
        self.assertNotEqual(dithered, non_dither)
        self.assertGreater(len(set(dithered.replace('\n', ''))), 1)
        self.assertEqual(dithered, photo_to_ascii(self.mid_gray, 32, 32,
                         settings=replace(self.settings, dither=True)))
        self.assertEqual([len(row) for row in dithered.splitlines()], [32] * 16)

    def test_edge_definition_affects_boundaries_but_not_uniform_input(self):
        no_edge = photo_to_ascii(self.mid_gray, 32, 32, settings=self.settings)
        with_edge = photo_to_ascii(self.mid_gray, 32, 32,
                                   settings=replace(self.settings, edge=100))
        self.assertEqual(no_edge, with_edge)
        split = gray_image(32, 32, lambda x, _y: 40 if x < 16 else 220)
        baseline = photo_to_ascii(split, 32, 32, settings=self.settings)
        enhanced = photo_to_ascii(split, 32, 32,
                                  settings=replace(self.settings, edge=100))
        self.assertNotEqual(baseline, enhanced)
        # Changes stay near the sharp vertical boundary, not across the field.
        self.assertEqual(baseline.splitlines()[8][:12], enhanced.splitlines()[8][:12])
        self.assertEqual(baseline.splitlines()[8][20:], enhanced.splitlines()[8][20:])

    def test_padding_remains_whitespace_even_with_advanced_controls(self):
        landscape = gray_image(64, 8, lambda x, _y: 30 if x < 32 else 220)
        opts = replace(self.settings, fit='fit', dither=True, gamma=1.7, edge=100)
        output = photo_to_ascii(landscape, 64, 8, settings=opts).splitlines()
        self.assertEqual(output[0], ' ' * 32)
        self.assertEqual(output[-1], ' ' * 32)
        self.assertTrue(any(c != ' ' for row in output for c in row))

    def test_validation_rejects_out_of_range_or_non_boolean_controls(self):
        for changed in ({'gamma': 0}, {'gamma': 2.51}, {'gamma': float('nan')},
                        {'edge': -1}, {'edge': 101}, {'dither': 'yes'}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                photo_to_ascii(self.mid_gray, 32, 32,
                               settings=replace(self.settings, **changed))

    def test_combined_advanced_modes_bound_output_to_ascii_grid(self):
        gradient = gray_image(32, 32, lambda x, y: min(255, x * 5 + y * 3))
        for ramp in RAMPS:
            opts = replace(self.settings, ramp=ramp, gamma=1.4,
                           edge=70, dither=True, invert=True)
            rendered = photo_to_ascii(gradient, 32, 32, settings=opts)
            self.assertEqual(len(rendered.splitlines()), 16)
            self.assertTrue(all(len(row) == 32 for row in rendered.splitlines()))
            self.assertTrue(set(rendered.replace('\n', '')).issubset(set(RAMPS[ramp])))


class AdvancedUIContracts(unittest.TestCase):
    def test_progressive_options_are_collapsed_and_part_of_live_preview(self):
        view = (SRC / 'photo_ascii_view.py').read_text()
        ast.parse(view)
        self.assertIn("Adw.ExpanderRow(title='Advanced image tools'", view)
        self.assertIn('self.advanced.set_expanded(False)', view)
        for signal in ("(self.gamma, 'notify::value')",
                       "(self.edge, 'notify::value')",
                       "(self.dither, 'notify::active')"):
            self.assertIn(signal, view)
        for value in ('gamma=round(self.gamma.get_value(), 1)',
                      'edge=int(self.edge.get_value())',
                      'dither=self.dither.get_active()'):
            self.assertIn(value, view)
        self.assertIn('def _reset_advanced(', view)
        self.assertIn('self.gamma.set_value(1.0)', view)
        self.assertIn('self.dither.set_active(False)', view)
        self.assertIn('GLib.timeout_add(80, self._refresh)', view)
        self.assertIn("narrow.add_setter(compare, 'orientation', Gtk.Orientation.VERTICAL)", view)
        self.assertIn('self._ensure_latest_preview()', view)
        self.assertNotIn('subprocess', view)

    def test_docs_and_version_are_recorded(self):
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertGreaterEqual(int(version.split('.')[1]), 88)
        self.assertIn(f'BUILD_VERSION = "{version}"', (SRC / 'build_info.py').read_text())
        for f in ('CHANGELOG.md', 'RELEASE-V88.md', 'ROADMAP.md', 'TASKS.md'):
            text = read_source(f)
            self.assertTrue('V88' in text or '0.88.0' in text, f)


if __name__ == '__main__':
    unittest.main()
