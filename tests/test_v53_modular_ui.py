"""Verify architectural boundaries without requiring a working GTK display."""
from _bootstrap import SRC, read_source  # noqa: F401
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = {
    "preferences_shell": {"_make_shell", "_make_navigation"},
    "preferences_controls": {"_make_common_widgets", "_make_monitor_widgets"},
    "preferences_pages": {"_layout_preferences", "_make_raw_playlist"},
    "preferences_gallery": {"_preview_effect", "_close_gallery"},
    "preferences_gallery_view": {"_make_gallery_cards", "_make_gallery_window"},
    "preferences_displays": {"_refresh_fit_warnings", "_update_monitor_controls"},
    "preferences_state": {"_preference_snapshot", "_load_preferences", "_on_save", "_mark_dirty"},
    "preferences_actions": {"_open_performance", "_set_notice", "_on_command"},
}

class ModularUITests(unittest.TestCase):
    def test_settings_is_orchestration_not_monolith(self):
        source = (SRC / 'settings.py').read_text()
        self.assertLess(len(source.splitlines()), 260)
        tree = ast.parse(source)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'SettingsWindow')
        init = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '__init__')
        source = ast.get_source_segment(source, init)
        for name in ('_make_shell', '_make_common_widgets', '_make_gallery_cards',
                     '_make_monitor_widgets', '_layout_preferences', '_make_gallery_window',
                     '_make_navigation', '_make_raw_playlist'):
            self.assertIn('self.' + name + '()', source)

    def test_controllers_implement_their_methods(self):
        for module, names in MODULES.items():
            with self.subTest(module=module):
                text = read_source(f'{module}.py')
                tree = ast.parse(text)
                defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
                self.assertTrue(names.issubset(defined), names - defined)

    def test_all_modules_are_installed(self):
        src = (ROOT / 'install.sh').read_text()
        for name in (*MODULES, 'preferences_model', 'effect_catalog'):
            self.assertRegex(src, rf'for module in [^\n]*\b{re.escape(name)}\b')

    def test_native_switch_rows_are_real_preferences_not_gtk_suffixes(self):
        pages = (SRC / 'preferences_controls.py').read_text() + (SRC / 'preferences_pages.py').read_text()
        self.assertIn('self.enabled = Adw.SwitchRow()', pages)
        self.assertIn('self.per_monitor = Adw.SwitchRow()', pages)
        self.assertIn('self.playlist_mode = Adw.SwitchRow()', pages)
        self.assertIn('self.section_groups[section].add(widget)', pages)
        state = (SRC / 'preferences_state.py').read_text()
        self.assertIn('(Gtk.Switch, Adw.SwitchRow)', state)

    def test_no_gtk_dependency_in_pure_model(self):
        source = (SRC / 'preferences_model.py').read_text()
        tree = ast.parse(source)
        imports = [alias.name.split('.')[0] for node in ast.walk(tree)
                   if isinstance(node, ast.Import) for alias in node.names]
        self.assertNotIn('gi', imports)
        self.assertNotIn('Gtk', source)
