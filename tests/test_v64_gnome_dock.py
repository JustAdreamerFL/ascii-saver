"""Tests for opt-in GNOME dock compatibility without touching live settings."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from gnome_dock import DockSettings, FULLSCREEN_PROFILE, SCHEMA, apply, inspect, restore


class FakeGSettings:
    def __init__(self, initial):
        self.values = dict(initial)
        self.calls = []

    def execute(self, argv):
        self.calls.append(tuple(argv))
        assert argv[:1] == ['gsettings']
        cmd = argv[1]
        if cmd == 'list-keys':
            return '\n'.join(self.values)
        if cmd == 'get':
            return self.values[argv[3]]
        if cmd == 'set':
            self.values[argv[3]] = argv[4]
            return ''
        raise AssertionError(argv)


class DockProfileTests(unittest.TestCase):
    def setUp(self):
        self.values = {"dock-fixed": "true", "autohide": "false",
                       "intellihide": "false", "intellihide-mode": "'FOCUS_APPLICATION_WINDOWS'",
                       "autohide-in-fullscreen": "true", "manualhide": "false"}
        self.runner = FakeGSettings(self.values)
        self.settings = DockSettings(self.runner.execute)
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'gnome-dock-backup.json'

    def tearDown(self):
        self.tmp.cleanup()

    def test_diagnostic_does_not_change_settings(self):
        message, values = inspect(self.settings)
        self.assertIn('differs', message)
        self.assertEqual(len(values), 5)
        self.assertEqual(self.runner.values, self.values)
        self.assertFalse(self.path.exists())

    def test_explicit_apply_then_restore_originals(self):
        self.assertIn('applied', apply(self.settings, self.path))
        for key, value in FULLSCREEN_PROFILE.items():
            self.assertEqual(self.runner.values[key], value)
        self.assertEqual(self.runner.values['manualhide'], 'false')
        self.assertTrue(self.path.exists())
        self.assertEqual(json.loads(self.path.read_text())['schema'], SCHEMA)
        self.assertIn('Restored 5', restore(self.settings, self.path))
        self.assertEqual(self.runner.values, self.values)
        self.assertFalse(self.path.exists())

    def test_second_apply_does_not_overwrite_original_backup(self):
        apply(self.settings, self.path)
        original = self.path.read_bytes()
        self.assertIn('backup already exists', apply(self.settings, self.path))
        self.assertEqual(original, self.path.read_bytes())

    def test_restore_does_not_overwrite_new_manual_change(self):
        apply(self.settings, self.path)
        self.runner.values['intellihide-mode'] = "'MAXIMIZED_WINDOWS'"
        result = restore(self.settings, self.path)
        self.assertIn('left untouched', result)
        self.assertEqual(self.runner.values['intellihide-mode'], "'MAXIMIZED_WINDOWS'")
        self.assertTrue(self.path.exists())
        # Returning to the applied state makes it safe to restore the original.
        self.runner.values['intellihide-mode'] = FULLSCREEN_PROFILE['intellihide-mode']
        restore(self.settings, self.path)
        self.assertFalse(self.path.exists())
        self.assertEqual(self.runner.values, self.values)

    def test_no_changes_needs_no_backup(self):
        runner = FakeGSettings(FULLSCREEN_PROFILE)
        settings = DockSettings(runner.execute)
        self.assertIn('already match', apply(settings, self.path))
        self.assertFalse(self.path.exists())

    def test_missing_optional_key_not_modified(self):
        runner = FakeGSettings({'dock-fixed': 'true'})
        settings = DockSettings(runner.execute)
        self.assertIn('applied', apply(settings, self.path))
        self.assertEqual(runner.values, {'dock-fixed': 'false'})
        self.assertIn('Restored 1', restore(settings, self.path))


if __name__ == '__main__':
    unittest.main()
