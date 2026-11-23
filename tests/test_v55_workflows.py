"""Regression tests for V55 main controls, rotation, and installer contracts."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401
import random
import unittest
from pathlib import Path
from unittest.mock import patch
import ctl
from effect_rotation import EffectShuffleBag
from preferences_defaults import is_factory_default

ROOT = Path(__file__).resolve().parents[1]

class PlaybackWorkflowTests(unittest.TestCase):
    def test_shuffled_rotation_uses_each_enabled_effect_before_repeating(self):
        bag = EffectShuffleBag(random.Random(123))
        names = ['beams', 'matrix', 'waves', 'print']
        first = [bag.next(names) for _ in range(4)]
        second = [bag.next(names) for _ in range(4)]
        self.assertEqual(set(first), set(names))
        self.assertEqual(set(second), set(names))
        self.assertNotEqual(first[-1], second[0])

    def test_shuffled_rotation_resets_after_enabled_effects_change(self):
        bag = EffectShuffleBag(random.Random(3))
        bag.next(['beams', 'matrix'])
        self.assertEqual(bag.next(['waves']), 'waves')
        with self.assertRaises(ValueError):
            bag.next([])

    def test_windowed_preview_pid_detection_only_for_real_saver(self):
        with patch.object(ctl, 'process_matches_installed_saver', return_value=True):
            with patch.object(Path, 'read_bytes', return_value=b'/usr/bin/python\0/app.py\0--windowed\0'):
                self.assertTrue(ctl.is_windowed_preview(1234))
            with patch.object(Path, 'read_bytes', return_value=b'/usr/bin/python\0/app.py\0'):
                self.assertFalse(ctl.is_windowed_preview(1234))
        with patch.object(ctl, 'process_matches_installed_saver', return_value=False):
            self.assertFalse(ctl.is_windowed_preview(1234))

    def test_main_preview_button_and_windowed_playlist_advances(self):
        src = (SRC / 'settings.py').read_text()
        app = (SRC / 'app.py').read_text()
        self.assertIn('"Close Preview" if status["preview"] else "Preview"', src)
        self.assertIn('self.app.preview_sequence.advance()', app)
        self.assertNotIn('("Stop the current animation", "Stop"', src)
        self.assertIn('not self.windowed else None', app)

    def test_reset_never_changes_row_allocation(self):
        src = (SRC / 'preferences_defaults.py').read_text()
        self.assertIn('reset.set_opacity', src)
        self.assertNotIn('reset.set_visible(not is_factory_default', src)
        self.assertFalse(is_factory_default(60, 120))

    def test_installer_persists_cargo_cache_and_bundles_modules(self):
        src = (ROOT / 'install.sh').read_text()
        self.assertIn('cargo_target_dir="$new_cache/cargo-target"', src)
        self.assertIn('new_cache="$cache_home/ascii-saver"', src)
        self.assertNotIn('"$transaction_dir/ttfx-target"', src)
        self.assertIn('"$py_src/effect_rotation.py"', src)
        self.assertIn('"$py_src/status_model.py"', src)

    def test_artwork_has_separate_select_edit_factory_reset(self):
        src = (SRC / 'preferences_controls.py').read_text()
        self.assertIn('def _edit_monitor_artwork', src)
        self.assertIn('Gtk.Button(label="Choose…")', src)
        self.assertIn('Gtk.Button(label="Edit")', src)
        self.assertIn('e.set_text("")', src)

    def test_failure_diagnostics_survive_startup(self):
        src = (SRC / 'ctl.py').read_text()
        self.assertIn('"renderer.log"', src)
        self.assertIn('"renderer.previous.log"', src)
        self.assertIn('os.O_RDWR | os.O_CREAT', src)

if __name__ == '__main__':
    unittest.main()
