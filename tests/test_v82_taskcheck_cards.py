"""V82 regression tests for user-observed card classification and watcher status."""
import ast
import unittest
from pathlib import Path
from unittest.mock import patch

from playlist_engine import EFFECTS, group
from effect_metadata import effect_caption
from status_model import automatic_activation_label, current_status

ROOT = Path(__file__).resolve().parents[1]


class ClassificationTests(unittest.TestCase):
    def test_all_37_effects_display_their_real_filter_categories(self):
        self.assertEqual(len(EFFECTS), 37)
        for effect in EFFECTS:
            c = group(effect)
            self.assertEqual(effect_caption(effect),
                             f"{c['duration'].capitalize()} · {c['intensity'].capitalize()}")

    def test_known_effects(self):
        self.assertEqual(effect_caption('waves'), 'Long · Gentle')
        self.assertEqual(effect_caption('matrix'), 'Long · Energetic')
        self.assertEqual(effect_caption('wipe'), 'Short · Gentle')

    def test_both_card_galleries_show_visible_metadata(self):
        library = (ROOT / 'preferences_gallery_view.py').read_text()
        editor = (ROOT / 'playlist_editor.py').read_text()
        self.assertIn('label=effect_caption(name)', library)
        self.assertIn('label=effect_caption(effect)', editor)
        self.assertIn('card.append(classification)', library)
        self.assertIn('tile.append(classification)', editor)
        self.assertIn('Suggested duration and intensity, not measured', library)
        self.assertIn('Suggested duration and intensity, not measured', editor)
        self.assertIn('"$source_dir/effect_metadata.py"', (ROOT / 'install.sh').read_text())


class ActivationStatusTests(unittest.TestCase):
    def test_paused_is_distinct_from_watcher_service(self):
        self.assertIn('Paused', automatic_activation_label(False, True))
        self.assertIn('Paused', automatic_activation_label(False, False))
        self.assertIn('Start Now', automatic_activation_label(False, False))
        self.assertIn('not detected', automatic_activation_label(True, False))
        self.assertIn('idle delay', automatic_activation_label(True, True))

    def test_status_uses_saved_config_not_pid_to_report_activation(self):
        with patch('status_model.ctl.current_pid', return_value=None), \
             patch('status_model.ctl.current_watcher_pid', return_value=456), \
             patch('status_model.load_config', return_value={'enabled': False}):
            result = current_status()
        self.assertIn('Paused', result['automatic'])
        self.assertIn('automatic launch disabled', result['watcher'])

    def test_dashboard_configure_does_not_mutate_unsaved_preferences(self):
        src = (ROOT / 'settings.py').read_text()
        self.assertIn('"Automatic activation", "Configure"', src)
        self.assertIn('application.open_preferences("general")', src)
        self.assertIn('self.automatic_row.set_subtitle(status["automatic"])', src)
        self.assertNotIn('ctl.update_config("enabled"', src)
        for item in ('settings.py','status_model.py','effect_metadata.py',
                     'playlist_editor.py','preferences_gallery_view.py'):
            ast.parse((ROOT / item).read_text())


class TrackingTests(unittest.TestCase):
    def test_single_checklist_reconciles_historical_hotplug(self):
        tasks = (ROOT / 'TASKS.md').read_text()
        old = (ROOT / 'docs/archive/UX-ROADMAP-V54.md').read_text()
        self.assertIn('ROADMAP.md', (ROOT / 'UX-ROADMAP.md').read_text())
        self.assertIn('- [x] Per-monitor controls added and removed', tasks)
        self.assertIn('- [x] Dynamically rebuild per-display', old)
        self.assertIn('- [ ] **E02/B213**', tasks)
        self.assertIn('runtime', tasks.lower())
        self.assertIn('0.82.0 (experimental) - 2026-11-07', (ROOT / 'CHANGELOG.md').read_text())
        self.assertGreaterEqual(tuple(map(int, (ROOT / 'VERSION').read_text().strip().split('.'))), (0, 82, 0))


if __name__ == '__main__':
    unittest.main()
