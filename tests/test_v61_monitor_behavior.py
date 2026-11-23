"""GTK-free and source-level tests for live monitor labels and cursor handling."""
from _bootstrap import SRC, read_source  # noqa: F401
import unittest
from pathlib import Path

from monitor_labels import playback_title, connected_displays

ROOT = Path(__file__).resolve().parents[1]

class MonitorBehaviorTests(unittest.TestCase):
    def test_singular(self):
        self.assertEqual(playback_title(1), "Start on this display")
        self.assertEqual(connected_displays(1), "1 display connected")

    def test_multiple(self):
        self.assertEqual(playback_title(2), "Start on all displays")
        self.assertEqual(connected_displays(3), "3 displays connected")

    def test_zero(self):
        self.assertEqual(playback_title(0), "Start screensaver")
        self.assertEqual(connected_displays(0), "0 displays connected")

    def test_gtk_hotplug_subscription(self):
        content = (SRC / "settings.py").read_text()
        self.assertGreaterEqual(content.count('"items-changed"'), 2)
        self.assertIn('self.start_row.set_title(playback_title(count))', content)
        self.assertIn('self._monitor_model.disconnect(self._monitor_handler)', content)
        self.assertIn('"$py_src/monitor_labels.py"', (ROOT / "install.sh").read_text())

    def test_cursor_reapplies_on_map_and_surface(self):
        content = (SRC / "app.py").read_text()
        self.assertIn('self.connect("map", self._on_mapped_for_cursor)', content)
        self.assertIn('surface.set_cursor(self._invisible_cursor)', content)

if __name__ == '__main__':
    unittest.main()
