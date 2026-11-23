from _bootstrap import SRC, read_source  # noqa: F401
from ui_sources import all_ui_source
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class V46SourceContracts(unittest.TestCase):
    def test_decoder_free_previews_are_viewport_controlled(self):
        source = (SRC / 'animated_preview.py').read_text()
        self.assertIn('Gdk.MemoryTexture.new', source)
        self.assertIn('PackedPreview(self._path)', source)
        self.assertIn("self.connect('unmap', self._unmapped)", source)
        self.assertIn('translate_coordinates(scroller', source)
        self.assertNotIn('GdkPixbufAnimation.new_from_file(', source)

    def test_preserve_ttfx_last_rendered_frame(self):
        source = (SRC / 'app.py').read_text()
        success_section = source.split('if tte_exit_ok(status):')[1].split('self.tte_failures += 1')[0]
        self.assertNotIn('self._show_finished_artwork()', success_section)

    def test_sticky_save_bar_and_monitor_controls(self):
        source = all_ui_source()
        self.assertIn('toolbar_view.add_bottom_bar(self.changes_tray)', source)
        self.assertIn('self.toast_overlay.set_child(self.nav_layout)', source)
        self.assertIn('preview_page.append(preview_group)', source)
        self.assertIn('tools_group = make_group("Tools")', source)
        self.assertNotIn('toolbar.append(self.unsaved_banner)', source)
        self.assertIn('self.monitor_revealer.set_reveal_child(independent or own_palette)', source)
        self.assertIn('self.gallery_window', source)

    def test_installer_includes_new_modules(self):
        install = (ROOT / 'install.sh').read_text()
        for name in ('animated_preview.py', 'artwork_fit.py'):
            self.assertIn(f'"$py_src/{name}"', install)

    def test_monitor_dropdown_updated_only_on_set_change(self):
        source = (SRC / 'performance_ui.py').read_text()
        self.assertIn('if monitors != self._last_monitor_ids:', source)


if __name__ == '__main__':
    unittest.main()
