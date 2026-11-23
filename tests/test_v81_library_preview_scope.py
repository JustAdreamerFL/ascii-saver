"""V81 regression contracts: one visible preview selector, stable preference state."""
from _bootstrap import SRC, read_source  # noqa: F401
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = (SRC / "preferences_controls.py").read_text(encoding="utf-8")
PAGES = (SRC / "preferences_pages.py").read_text(encoding="utf-8")
GALLERY = (SRC / "preferences_gallery_view.py").read_text(encoding="utf-8")
STATE = (SRC / "preferences_state.py").read_text(encoding="utf-8")
GALLERY_LOGIC = (SRC / "preferences_gallery.py").read_text(encoding="utf-8")

class PreviewScopeTests(unittest.TestCase):
    def test_one_visible_play_mode_selector_in_effect_library_only(self):
        self.assertNotIn('("preview", "Effect Library Play opens", self.effect_preview_mode)', PAGES)
        self.assertNotIn('("preview", "Preview behavior",', CONTROLS)
        self.assertIn('self.library_preview_mode = Gtk.DropDown.new_from_strings([', GALLERY)
        self.assertIn('preview_mode_row.append(self.library_preview_mode)', GALLERY)
        self.assertIn('preview_page.append(preview_group)', GALLERY)
        self.assertIn('adaptive_action_row(preview_group, "Effect preview mode", self.effect_preview_mode)', GALLERY)
        self.assertIn('tools.append(tools_group)', PAGES)

    def test_saved_preview_modes_and_library_partial_save_are_unchanged(self):
        self.assertIn('self.effect_preview_mode = Gtk.DropDown.new_from_strings([', CONTROLS)
        self.assertIn('self.library_preview_mode.set_selected(self.effect_preview_mode.get_selected())', STATE)
        self.assertIn('self.effect_preview_mode.connect("notify::selected", self._mark_dirty)', STATE)
        self.assertIn('self.effect_preview_mode.connect("notify::selected", self._mark_library_dirty)', STATE)
        self.assertIn('"window" if self.library_preview_mode.get_selected() == 0 else "inline"', GALLERY_LOGIC)
        self.assertIn('self.effect_preview_mode.set_selected(selected)', GALLERY_LOGIC)
        self.assertIn('self._saved_snapshot, self._preference_snapshot(), (4, 6)', GALLERY_LOGIC)

    def test_changelog_contains_complete_chronological_recent_releases(self):
        changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
        import re
        headings = [int(version) for version in re.findall(r'^## 0\.(\d+)\.0\b', changelog, flags=re.MULTILINE)]
        newest = int((ROOT / 'VERSION').read_text().strip().split('.')[1])
        self.assertEqual(headings[:newest - 65], list(range(newest, 65, -1)))
        self.assertEqual(headings, sorted(set(headings), reverse=True))
        for version in range(66, newest + 1):
            self.assertIn(f'## 0.{version}.0', changelog)

    def test_python_sources_parse(self):
        for src in (CONTROLS, PAGES, GALLERY, STATE, GALLERY_LOGIC):
            ast.parse(src)

if __name__ == '__main__':
    unittest.main()
