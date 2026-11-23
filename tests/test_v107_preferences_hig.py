"""V107 user screenshot regression: prevent minimum-width overflow and status clutter.

GTK/Wayland acceptance still requires a real desktop with libadwaita.
"""
import ast
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def source(name): return (ROOT/name).read_text()

class PreferencesHIGTests(unittest.TestCase):
    def test_only_one_category_selector_in_header(self):
        shell = source('preferences_shell.py')
        self.assertIn('Gtk.DropDown.new_from_strings', shell)
        self.assertIn('header.set_title_widget(title_box)', shell)
        self.assertIn('self.navigation_list = Gtk.ListBox()', shell)
        self.assertNotIn('Adw.ViewSwitcher(', shell)
        self.assertNotIn('Adw.ViewSwitcherBar(', shell)
        self.assertEqual(shell.count('self.compact_categories.connect("notify::selected"'), 1)
        self.assertIn('self.set_size_request(360, 320)', shell)

    def test_preferences_have_no_service_polling_or_duplicated_runtime_states(self):
        shell=source('preferences_shell.py')
        settings=source('settings.py')
        self.assertNotIn('general.append(status_group)', shell)
        self.assertNotIn('general.append(tools_group)', shell)
        self.assertNotIn('general.append(files_group)', shell)
        self.assertNotIn('GLib.timeout_add_seconds(2, self._refresh_status)',settings.split('class DashboardWindow')[0])
        self.assertIn('GLib.timeout_add_seconds(2, self._refresh_status)',settings.split('class DashboardWindow')[1])

    def test_controls_not_in_horizontal_suffixes_at_narrow_width(self):
        ui=source('adwaita_ui.py')
        controls=source('preferences_controls.py')
        self.assertIn('self.layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL',ui)
        for identifier in ('rate_row', 'palette_row', 'artwork_row'):
            self.assertIn(identifier + ' = adaptive_action_row(',controls)
        self.assertNotIn('set_size_request(220, -1)', ui)

    def test_palette_advanced_collapsed_without_losing_controls(self):
        pages=source('preferences_pages.py')
        self.assertIn('self.palette_advanced = Adw.ExpanderRow(',pages)
        self.assertIn('self.palette_advanced.add_row(widget)',pages)
        self.assertIn('self.palette_advanced.add_row(row)',pages)
        for key in ('"Cycle through palette colors"','"Reverse palette at the ends"',
                    '"Effects per color transition"','"Shared palette"'):
            self.assertIn(key,pages)

    def test_save_only_when_dirty_and_messages_not_permanent(self):
        shell=source('preferences_shell.py')
        state=source('preferences_state.py')
        actions=source('preferences_actions.py')
        self.assertIn('self.unsaved_banner.set_visible(False)',shell)
        self.assertIn('self.banner_label.set_visible(False)', shell)
        self.assertIn('Gtk.Button(label="Discard")', shell)
        self.assertIn('self.changes_tray.set_visible(is_dirty)',state)
        self.assertIn('self.changes_tray.set_visible(False)',state)
        self.assertNotIn('general.append(self.notice)',shell)
        self.assertIn('self.toast_overlay.add_toast(toast)',actions)

    def test_diagnostics_and_artwork_actions_still_reachable_in_tools_menu(self):
        menu=source('app_menu.py')
        app=source('application_actions.py')
        page=source('preferences_pages.py')
        for method in ('self._edit_default_artwork', 'self._open_performance',
                       'self._open_duration_profiles', 'self._open_diagnostics'):
            self.assertIn(method, page)
        self.assertIn('tools.append(tools_group)', page)
        self.assertNotIn("menu.append_section('Tools'", menu)
        for handler in ("'edit-artwork':", "'performance':", "'measurements':", "'diagnostics':"):
            self.assertIn(handler,app)

    def test_modified_code_parse(self):
        for name in ('preferences_shell.py','preferences_pages.py','preferences_controls.py',
                     'adwaita_ui.py','preferences_actions.py','application_actions.py',
                     'app_menu.py','settings.py','preferences_state.py'):
            ast.parse(source(name))
