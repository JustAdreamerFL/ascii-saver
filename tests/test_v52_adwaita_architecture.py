"""Source contracts for V52 Adwaita migration, no GTK runtime needed."""
from ui_sources import all_ui_source

from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parent.parent


class AdwaitaArchitectureTests(unittest.TestCase):
    def test_real_preference_pages_groups_and_rows(self):
        helpers = (ROOT / 'adwaita_ui.py').read_text()
        self.assertIn('class SettingsPage(Adw.PreferencesPage)', helpers)
        self.assertIn('Adw.PreferencesGroup(title=title)', helpers)
        self.assertIn('Adw.ActionRow(title=title)', helpers)
        self.assertIn('row.set_activatable_widget(widget)', helpers)
        settings = all_ui_source()
        self.assertIn('page = SettingsPage(', settings)
        self.assertIn('self.sections.add_titled(page, name, title)', settings)
        self.assertIn('page_info.set_icon_name(icon)', settings)
        self.assertIn('adaptive_action_row(self.section_groups[section], label, widget', settings)
        self.assertNotIn('status_frame = Gtk.Frame', settings)
        self.assertNotIn('section_grids[section].attach', settings)

    def test_advanced_preferences_use_adwaita_expanders(self):
        settings = all_ui_source()
        self.assertIn('advanced = Adw.ExpanderRow(', settings)
        self.assertIn('def _open_raw_playlist_editor', settings)
        self.assertIn('advanced.add_row(nested)', settings)
        self.assertIn('window.set_content(toolbar)', settings)

    def test_action_rows_preserve_configuration_widgets(self):
        helpers = (ROOT / 'adwaita_ui.py').read_text()
        self.assertIn('row.add_suffix(widget)', helpers)
        settings = all_ui_source()
        self.assertIn('self.per_monitor.connect("notify::active", self._update_monitor_controls)', settings)
        self.assertIn('self._preference_snapshot() != self._saved_snapshot', settings)
        self.assertIn('def _on_save', settings)
        self.assertIn('def _discard_changes', settings)
        self.assertIn('"monitor_visuals":', settings)

    def test_adaptive_playlist_editor_and_controls(self):
        source = (ROOT / 'playlist_editor.py').read_text()
        self.assertIn('class Editor(Adw.ApplicationWindow)', source)
        self.assertIn('columns = Adw.NavigationSplitView()', source)
        self.assertIn('Adw.NavigationPage(child=sidebar_toolbar, title="Playlists")', source)
        self.assertIn('Adw.NavigationPage(child=content_toolbar, title="Effect gallery")', source)
        self.assertIn('narrow.add_setter(columns, "collapsed", True)', source)
        self.assertIn('self.columns.set_show_content(True)', source)
        self.assertIn('Adw.EntryRow(title="Playlist name")', source)
        self.assertIn('Adw.SwitchRow(title="Enabled")', source)

    def test_specialized_windows_use_adwaita_chrome(self):
        for name, marker in (
            ('effect_preview_window.py', 'class EffectPreviewWindow(Adw.Window)'),
            ('performance_ui.py', 'class PerformanceWindow(Adw.Window)'),
        ):
            source = (ROOT / name).read_text()
            self.assertIn(marker, source)
            if name == 'effect_preview_window.py':
                self.assertIn('toolbar.add_top_bar(header)', source)
                self.assertIn('header.set_title_widget(self.title_label)', source)
            else:
                self.assertIn('toolbar.add_top_bar(Adw.HeaderBar())', source)
            self.assertIn('self.set_content(toolbar)', source)
        settings = all_ui_source()
        self.assertIn('self.gallery_window = Adw.Window(', settings)
        self.assertIn('self.gallery_window.set_content(self.library_toast_overlay)', settings)
        self.assertIn('library_overlay.set_child(library_toolbar_view)', settings)
        self.assertIn('class SettingsApplication(ApplicationActionsMixin, Adw.Application)', settings)

    def test_unsaved_state_and_feedback_behave_with_native_chrome(self):
        source = all_ui_source()
        self.assertIn('self.toast_overlay = Adw.ToastOverlay()', source)
        self.assertIn('toolbar_view.add_bottom_bar(self.changes_tray)', source)
        self.assertIn('self.toast_overlay.add_toast(toast)', source)
        self.assertIn('self.changes_tray.set_reveal_child(is_dirty)', source)
        self.assertIn('banner_save.add_css_class("suggested-action")', source)

    def test_installer_copies_ui_module(self):
        source = (ROOT / 'install.sh').read_text()
        self.assertIn('install -m 0644 "$source_dir/adwaita_ui.py" "$staged_app/adwaita_ui.py"', source)


if __name__ == '__main__':
    unittest.main()
