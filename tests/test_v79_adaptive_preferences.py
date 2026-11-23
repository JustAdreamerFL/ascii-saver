"""Regression tests for narrow Preferences layouts, updated for V107's no-tabs design."""
from _bootstrap import SRC, read_source  # noqa: F401
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = (SRC / 'preferences_shell.py').read_text()
CONTROLS = (SRC / 'preferences_controls.py').read_text()
PAGES = (SRC / 'preferences_pages.py').read_text()
UI = (SRC / 'adwaita_ui.py').read_text()

class AdaptiveNavigationTests(unittest.TestCase):
    def test_one_header_selector_has_no_huge_tab_minimum_width(self):
        self.assertIn('header.set_title_widget(title_box)', SHELL)
        self.assertIn('self.wide_sidebar.set_visible(False)', SHELL)
        self.assertNotIn('ViewSwitcher(', SHELL)
        self.assertNotIn('ViewSwitcherBar(', SHELL)
        self.assertIn('self.set_size_request(360, 320)', SHELL)

    def test_all_categories_reachable_and_selector_tracks_page(self):
        for key in ('general', 'appearance', 'displays', 'animations', 'preview'):
            self.assertIn('"' + key + '"', SHELL)
        self.assertIn('self.sections.set_visible_child_name(names[index])', SHELL)
        self.assertIn('self.sections.connect("notify::visible-child-name", reflect_section)', SHELL)

    def test_dirty_actions_remain_accessible_without_saved_status_footer(self):
        self.assertIn('banner_save.connect("clicked", self._on_save)', SHELL)
        self.assertIn('self.banner_discard.connect("clicked", self._discard_changes)', SHELL)
        self.assertIn('toolbar_view.add_bottom_bar(self.changes_tray)', SHELL)
        self.assertNotIn('Gtk.Label(label="Changes saved"', SHELL)
        state = (SRC / 'preferences_state.py').read_text()
        self.assertIn('self.changes_tray.set_visible(is_dirty)', state)

    def test_sliders_do_not_force_wide_rows(self):
        self.assertNotIn('set_size_request(220, -1)', UI + PAGES)
        self.assertIn('widget.set_size_request(110, -1)', UI)
        self.assertIn('widget.set_size_request(110, -1)', PAGES)
        self.assertIn('widget.set_hexpand(True)', UI)
        self.assertIn('widget.set_hexpand(True)', PAGES)

    def test_long_monitor_suffixes_wrap_instead_of_clipping(self):
        self.assertIn('swatches = Gtk.FlowBox()', CONTROLS)
        self.assertIn('picker_box = Gtk.FlowBox()', CONTROLS)
        self.assertIn('picker_box.set_min_children_per_line(1)', CONTROLS)
        self.assertIn('picker_box.set_max_children_per_line(4)', CONTROLS)
        self.assertIn('picker_box.insert(item, -1)', CONTROLS)

    def test_compact_preview_mode_labels_keep_saved_values_identical(self):
        self.assertIn('"Separate window"', CONTROLS)
        self.assertIn('"Pinned in library"', CONTROLS)
        gallery = (SRC / 'preferences_gallery.py').read_text()
        state = (SRC / 'preferences_state.py').read_text()
        self.assertIn('"window" if self.library_preview_mode.get_selected() == 0 else "inline"', gallery)
        self.assertIn('"window" if self.effect_preview_mode.get_selected() == 0 else "inline"', state)

    def test_all_modified_files_parse(self):
        for source in (SHELL, CONTROLS, PAGES, UI):
            ast.parse(source)

if __name__ == '__main__':
    unittest.main()
