"""Regression tests for GNOME Shell cursor bridge: no GTK or Shell required."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from gnome_cursor_bridge import FULLSCREEN_BUS_NAME, FullscreenCursorLease

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / 'gnome-shell-extension' / 'ascii-saver-cursor@ascii-saver.local'


class GioStub:
    class BusNameOwnerFlags:
        NONE = 0

    def __init__(self):
        self.calls = []

    def bus_own_name_on_connection(self, *args):
        self.calls.append(('own', args))
        return 42

    def bus_unown_name(self, owner):
        self.calls.append(('unown', owner))


class CursorLeaseTests(unittest.TestCase):
    def test_owner_acquire_idempotent_release_idempotent(self):
        gio = GioStub()
        lease = FullscreenCursorLease(gio, object(), enabled=True)
        self.assertTrue(lease.acquire())
        self.assertTrue(lease.acquire())
        self.assertEqual(len([c for c in gio.calls if c[0] == 'own']), 1)
        self.assertEqual(gio.calls[0][1][1], FULLSCREEN_BUS_NAME)
        lease.release()
        lease.release()
        self.assertEqual(gio.calls[-1], ('unown', 42))
        self.assertEqual(len(gio.calls), 2)

    def test_preview_and_kde_cannot_acquire(self):
        gio = GioStub()
        self.assertFalse(FullscreenCursorLease(gio, object(), enabled=False).acquire())
        self.assertFalse(FullscreenCursorLease(gio, None, enabled=True).acquire())
        self.assertEqual(gio.calls, [])

    def test_app_requires_mapped_fullscreen_and_releases_for_lock(self):
        source = (ROOT / 'app.py').read_text()
        self.assertIn('self.app._announce_cursor_lease()', source)
        self.assertIn('not self.windowed and self._screen_lock_backend == GNOME', source)
        self.assertIn('any(window.get_mapped()', source)
        self.assertIn('self._cursor_lease.release()', source)
        self.assertIn('if active:\n            self.quit_saver()', source)

    def test_shell_extension_has_paired_hide_and_show_and_crash_recovery(self):
        metadata = json.loads((EXT / 'metadata.json').read_text())
        self.assertEqual(metadata['uuid'], EXT.name)
        self.assertIn('49', metadata['shell-version'])
        source = (EXT / 'extension.js').read_text()
        self.assertIn(FULLSCREEN_BUS_NAME, source)
        self.assertIn('Gio.bus_watch_name(', source)
        self.assertIn('inhibit_cursor_visibility()', source)
        self.assertIn('uninhibit_cursor_visibility()', source)
        self.assertIn('Main.screenShield?.locked', source)
        self.assertIn('Gio.bus_unwatch_name(', source)

    def test_no_automatic_extension_install(self):
        installer = (ROOT / 'install.sh').read_text()
        self.assertIn('gnome_cursor_bridge.py', installer)
        self.assertNotIn('gnome-extensions enable', installer)
        self.assertTrue((ROOT / 'scripts' / 'install-gnome-cursor-bridge.sh').exists())


if __name__ == '__main__':
    unittest.main()
