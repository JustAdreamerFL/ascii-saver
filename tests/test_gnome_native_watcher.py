"""Contracts for the optional, GNOME-specific native idle daemon."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class GnomeNativeWatcherTests(unittest.TestCase):
    def test_mutter_protocol(self):
        source = (ROOT / "gnome_idle_watcher.c").read_text()
        for symbol in ("org.gnome.Mutter.IdleMonitor", "AddIdleWatch", "AddUserActiveWatch",
                       "WatchFired", "RemoveWatch", "GetIdletime", "GLib", "GSubprocess"):
            # Actual GLib APIs have g_ prefixes; the implementation uses GIO.
            if symbol == "GLib":
                symbol = "g_main_loop_run"
            self.assertIn(symbol, source)
        self.assertNotIn("PyGObject", source)

    def test_installer_selects_native_backend(self):
        installer = (ROOT / "install.sh").read_text()
        self.assertIn("gnome_idle_watcher.c", installer)
        self.assertIn('pkg-config --cflags gio-2.0 json-glib-1.0', installer)
        self.assertIn('if [[ "$backend" == kde ]]', installer)
        self.assertIn('service_source="$source_dir/gnome-ascii-saver.service"', installer)
        self.assertNotIn('"$source_dir/gnome_idle_watcher.py"', installer)


if __name__ == "__main__":
    unittest.main()
