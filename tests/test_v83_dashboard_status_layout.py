"""A05 user-reported cramped/narrow dashboard status regression."""
from _bootstrap import SRC, read_source  # noqa: F401
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class DashboardStatusLayoutTests(unittest.TestCase):
    def test_dashboard_and_preferences_have_bounded_single_line_status(self):
        ui_helper = (SRC / "adwaita_ui.py").read_text()
        self.assertIn('indicator.set_single_line_mode(True)', ui_helper)
        self.assertIn('indicator.set_max_width_chars(24)', ui_helper)
        self.assertIn('indicator.set_ellipsize(Pango.EllipsizeMode.END)', ui_helper)
        src = (SRC / "settings.py").read_text()
        self.assertIn('compact_status_labels(self.renderer_status, self.watcher_status)', src)
        self.assertNotIn('action_row(status_group, "Renderer"', (SRC / 'preferences_shell.py').read_text())
        ast.parse(src)
        ast.parse(ui_helper)

    def test_full_status_remains_accessible_and_automatic_state_not_omitted(self):
        ui_helper = (SRC / "adwaita_ui.py").read_text()
        self.assertIn('label.set_tooltip_text(value)', ui_helper)
        src = (SRC / "settings.py").read_text()
        self.assertIn('set_status_labels((self.renderer_status, self.watcher_status)', src)
        dashboard = (SRC / "settings.py").read_text()
        self.assertIn('self.automatic_row.set_subtitle(status["automatic"])', dashboard)

    def test_version_and_changelog_registered(self):
        self.assertGreaterEqual(tuple(map(int, (ROOT/'VERSION').read_text().strip().split('.'))), (0, 83, 0))
        self.assertIn('## 0.83.0 (experimental) - 2026-11-07', (ROOT/'CHANGELOG.md').read_text())
        self.assertIn('A05', (ROOT/'MASTER-BACKLOG.md').read_text())

if __name__ == '__main__':
    unittest.main()
