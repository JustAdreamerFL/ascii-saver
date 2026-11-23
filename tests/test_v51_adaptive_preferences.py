"""Offline contracts for V51 libadwaita navigation and preview lifecycle."""
from _bootstrap import SRC, read_source  # noqa: F401
from ui_sources import all_ui_source

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = all_ui_source()


class AdaptivePreferencesTests(unittest.TestCase):
    def test_dashboard_and_preferences_are_separate_application_windows(self):
        tree = ast.parse(SETTINGS)
        names = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
        self.assertIn('DashboardWindow', names)
        self.assertIn('SettingsWindow', names)
        self.assertIn('Adw.ApplicationWindow', SETTINGS)
        self.assertIn('self.dashboard_window = DashboardWindow(self)', SETTINGS)
        self.assertIn('self.preferences_window = SettingsWindow(self)', SETTINGS)

    def test_five_adaptive_libadwaita_categories(self):
        for name, heading in (
            ('general', 'General'), ('appearance', 'Appearance'),
            ('displays', 'Displays'), ('animations', 'Animations'),
            ('preview', 'Preview'),
        ):
            self.assertIn(f'("{name}", "{heading}",', SETTINGS)
        self.assertIn('self.sections = Adw.ViewStack()', SETTINGS)
        self.assertIn('self.compact_categories = Gtk.DropDown.new_from_strings(', SETTINGS)
        self.assertIn('self.sections.connect("notify::visible-child-name", reflect_section)', SETTINGS)
        self.assertNotIn('Adw.ViewSwitcher(stack=self.sections)', SETTINGS)
        self.assertNotIn('Adw.ViewSwitcherBar(stack=self.sections)', SETTINGS)

    def test_preferences_switches_preserve_all_settings(self):
        for target in ('self.section_groups[section].add(widget)', 'appearance.append(palette_note)',
                       'displays.append(self.monitor_revealer)',
                       'animations.append(advanced_group)', 'preview_page.append(preview_group)',
                       'self._page_boxes["animations"].append(group)'):
            self.assertIn(target, SETTINGS)
        self.assertIn('toolbar_view.add_bottom_bar(self.changes_tray)', SETTINGS)
        self.assertIn('self._mark_saved()', SETTINGS)
        self.assertIn('self._discard_changes', SETTINGS)

    def test_preview_replay_and_shutdown(self):
        self.assertIn('Gtk.Button(label="Replay last effect")', SETTINGS)
        self.assertIn('self._last_preview_effect = effect', SETTINGS)
        self.assertIn('self._preview_effect(None, self._last_preview_effect)', SETTINGS)
        self.assertIn('self._effect_preview_window.close()', SETTINGS)
        self.assertIn('app.preferences_window.close()', SETTINGS)
        self.assertIn('self._stop_effect_preview()', SETTINGS)

    def test_cli_settings_route_and_dependency(self):
        self.assertIn('flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE', SETTINGS)
        self.assertIn('if "--preferences" in args:', SETTINGS)
        self.assertIn('return SettingsApplication().run(sys.argv)', SETTINGS)
        self.assertIn('[str(settings_launcher)]', (SRC / 'ctl.py').read_text())
        self.assertIn('preferences "$@"', (ROOT/'bin/ascii-saver-settings').read_text())
        installer = (ROOT/'install.sh').read_text()
        self.assertIn('("Adw", "1")', installer)
        self.assertIn('libadwaita', installer)


if __name__ == '__main__':
    unittest.main()
