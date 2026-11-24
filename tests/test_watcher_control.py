import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _bootstrap import SRC  # noqa: F401

import ctl


class WatcherControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.system_autostart = root / "etc" / "watcher.desktop"
        self.user_autostart = root / "config" / "autostart" / "watcher.desktop"
        self.autostart = self.user_autostart
        self.patches = [
            patch.object(ctl, "package_dir", str(root / "package")),
            patch.object(ctl, "system_autostart_file", self.system_autostart),
            patch.object(ctl, "user_autostart_file", self.user_autostart),
            patch.object(ctl, "autostart_file", self.autostart),
            patch.object(ctl, "systemd_user_available", return_value=False),
            patch.object(ctl, "current_watcher_pid", return_value=None),
            patch.object(ctl, "_start_watcher", return_value=True),
            patch.object(ctl, "_stop_watcher", return_value=None),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_disabled_toggle_masks_system_autostart(self):
        self.system_autostart.parent.mkdir(parents=True)
        self.system_autostart.write_text("[Desktop Entry]\n", encoding="utf-8")
        self.assertTrue(ctl.autostart_configured())
        ok, _ = ctl.set_watcher_enabled(False)
        self.assertTrue(ok)
        self.assertTrue(self.user_autostart.is_file())
        self.assertIn("Hidden=true", self.user_autostart.read_text(encoding="utf-8"))
        self.assertFalse(ctl.autostart_configured())

    def test_enabled_toggle_removes_user_mask(self):
        self.system_autostart.parent.mkdir(parents=True)
        self.system_autostart.write_text("[Desktop Entry]\n", encoding="utf-8")
        self.user_autostart.parent.mkdir(parents=True)
        self.user_autostart.write_text("[Desktop Entry]\nHidden=true\n", encoding="utf-8")
        self.assertFalse(ctl.autostart_configured())
        ok, _ = ctl.set_watcher_enabled(True)
        self.assertTrue(ok)
        self.assertFalse(self.user_autostart.exists())
        self.assertTrue(ctl.autostart_configured())

    def test_watcher_state_reports_configured_login(self):
        self.system_autostart.parent.mkdir(parents=True)
        self.system_autostart.write_text("[Desktop Entry]\n", encoding="utf-8")
        active, detail = ctl.watcher_state()
        self.assertFalse(active)
        self.assertIn("next login", detail)


if __name__ == "__main__":
    unittest.main()
