"""V108: focused palette, selection, history, closing and layout regressions.

All behavioral tests run headlessly without GTK and validate the real state
helpers used in UI handlers. Window contracts are static until live GTK tests.
"""
from _bootstrap import SRC, read_source  # noqa: F401
import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))

from artwork_history import read_history, remember_artwork, MAX_RECENT
from artwork_retouch import paint_selection
from artwork_selection import choose_surprise, prioritize_selection
from helpers import DEFAULT_CONFIG, load_config
from palette_engine import palette_color_for_round, palette_for_monitor
from palette_editor_model import validate_palette, reset_colors, add_color, remove_color, MAX_COLORS
from window_shortcuts import is_close_shortcut


def src(name): return read_source(name)


class PaletteBehavior(unittest.TestCase):
    def test_reset_is_factory_not_current_saved_value(self):
        self.assertEqual(reset_colors(), tuple(DEFAULT_CONFIG['palette']))
        self.assertNotEqual(reset_colors(), ('#112233',))

    def test_add_remove_and_bounds(self):
        colors=('#112233',)
        for _ in range(MAX_COLORS-1):
            colors=add_color(colors)
        self.assertEqual(len(colors),MAX_COLORS)
        with self.assertRaises(ValueError): add_color(colors)
        for _ in range(MAX_COLORS-1): colors=remove_color(colors)
        self.assertEqual(len(colors),1)
        with self.assertRaises(ValueError): remove_color(colors)

    def test_reject_unusable_or_wrong_palette_values(self):
        for bad in ([], 10, [None], ['red'], ['#123'], [123], ['#000000']*9):
            with self.subTest(bad=bad), self.assertRaises(ValueError): validate_palette(bad)
        self.assertEqual(validate_palette(['#abcdef']),('#ABCDEF',))

    def test_shared_and_independent_palettes_resolve_separately(self):
        config={**DEFAULT_CONFIG, 'palette':['#123456','#ABCDEF'],
                'monitor_visuals':{'DP-1':{'palette':['#F0F0F0','#101010']}}}
        self.assertEqual(palette_for_monitor(config,'DP-1'),('#123456','#ABCDEF'))
        config['per_monitor_visuals']=True
        self.assertEqual(palette_for_monitor(config,'DP-1'),('#F0F0F0','#101010'))
        self.assertEqual(palette_for_monitor(config,'DP-2'),('#123456','#ABCDEF'))
        self.assertEqual(palette_for_monitor(config,None),('#123456','#ABCDEF'))

    def test_round_color_changes_when_cycle_is_on(self):
        config={**DEFAULT_CONFIG,'palette':['#000000','#FFFFFF'],'palette_steps':1,
                'cycle_palette':True}
        self.assertEqual(palette_color_for_round(config,None,0),'#000000')
        self.assertEqual(palette_color_for_round(config,None,1),'#FFFFFF')
        config['cycle_palette']=False
        self.assertEqual(palette_color_for_round(config,None,1),'#000000')

    def test_saved_static_palette_remains_static(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.json'
            path.write_text(json.dumps({'cycle_palette':False,'palette_mode':'static',
                                       'palette':['#111111','#222222']}))
            loaded=load_config(path)
            self.assertFalse(loaded['cycle_palette'])
            self.assertEqual(palette_color_for_round(loaded,None,1),'#111111')

    def test_switch_and_reset_are_reachable_in_appearance(self):
        controls=src('preferences_controls.py')
        pages=src('preferences_pages.py')
        state=src('preferences_state.py')
        for needle in ('Gtk.FlowBox()', 'Gtk.Button(label="Add color")',
                       'Gtk.Button(label="Remove last")',
                       'Restore default palette', '_update_shared_reset'):
            self.assertIn(needle,controls)
        self.assertIn('Different palettes on each display',pages)
        self.assertIn('per_monitor_visuals',state)
        self.assertIn('self._replace_shared_palette',state)


class SelectionBehavior(unittest.TestCase):
    def test_surprise_picks_a_different_item_when_possible(self):
        self.assertEqual(choose_surprise(['one','two'],'one',lambda choices: choices[0]),'two')
        self.assertIsNone(choose_surprise([]))
        self.assertEqual(choose_surprise(['one'],'one'),'one')

    def test_surprise_is_visible_in_paged_results(self):
        assets=[SimpleNamespace(number=i) for i in range(600)]
        chosen=prioritize_selection(assets,596)
        self.assertEqual(chosen[0].number,596)
        self.assertEqual(len(chosen),len(assets))
        self.assertEqual(len(set(x.number for x in chosen)),600)
        self.assertEqual([x.number for x in chosen[1:5]],[0,1,2,3])

    def test_stale_surprise_selection_does_not_disturb_sorting(self):
        assets=[SimpleNamespace(number=i) for i in range(5)]
        self.assertEqual([x.number for x in prioritize_selection(assets,999)],list(range(5)))

    def test_online_selection_updates_gtk_list_and_preview(self):
        ui=src('artwork_online_view.py')
        self.assertIn('prioritize_selection(self._matches, previous)',ui)
        self.assertIn('self.listbox.select_row(chosen)',ui)
        self.assertIn('self.preview.get_buffer().set_text(item.artwork)',ui)


class ArtworkEditing(unittest.TestCase):
    def test_selected_area_fills_without_damaging_line_breaks(self):
        self.assertEqual(paint_selection('ab \n cd\n', '@'), '@@@\n@@@\n')
        self.assertEqual(paint_selection('a\nb', '?', erase=True), ' \n ')
        with self.assertRaises(ValueError): paint_selection('hi','é')

    def test_canvas_allows_click_drag_and_keyboard_undo(self):
        canvas=src('artwork_canvas_view.py')
        for needle in ('click.connect(\'released\', self._click_released)',
                       'drag.connect(\'drag-update\', self._drag_update)',
                       'line_cells(*self._previous_cell, *cell)',
                       'self.on_commit(updated)'):
            self.assertIn(needle,canvas)
        editor=src('artwork_editor.py')
        self.assertIn('self.draw_mode.set_active(True)',editor)
        self.assertIn('buf.begin_user_action()',editor)


class RecentArtwork(unittest.TestCase):
    def test_remembers_used_artwork_in_recency_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'artworks').mkdir()
            first=root/'artworks'/'first.txt';second=root/'artworks'/'second.txt'
            first.write_text('first');second.write_text('second')
            self.assertTrue(remember_artwork(root,first))
            self.assertFalse(remember_artwork(root,first))
            self.assertTrue(remember_artwork(root,second))
            self.assertEqual(read_history(root),['artworks/second.txt','artworks/first.txt'])
            self.assertTrue(remember_artwork(root,first))
            self.assertEqual(read_history(root),['artworks/first.txt','artworks/second.txt'])

    def test_invalid_and_external_paths_are_not_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'config';root.mkdir()
            external=Path(tmp)/'other.txt'; external.write_text('external')
            self.assertFalse(remember_artwork(root,external))
            (root/'artworks').mkdir()
            (root/'artworks'/'link.txt').symlink_to(external)
            self.assertFalse(remember_artwork(root,root/'artworks'/'link.txt'))
            self.assertEqual(read_history(root),[])

    def test_corrupted_history_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'artwork-history.json').write_text('{bogus')
            self.assertEqual(read_history(root),[])

    def test_history_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'artworks').mkdir()
            for i in range(MAX_RECENT+8):
                p=root/'artworks'/f'{i}.txt';p.write_text('x')
                remember_artwork(root,p)
            self.assertEqual(len(read_history(root)),MAX_RECENT)
            self.assertEqual(read_history(root)[0],f'artworks/{MAX_RECENT+7}.txt')

    def test_history_view_shows_default_and_last_used(self):
        ui=src('artwork_library_view.py')
        self.assertIn("'Recently used'",ui)
        self.assertIn('read_history(self.config_dir)',ui)
        self.assertIn("'logo.txt', 'Default artwork'",ui)
        self.assertIn('self._recent_references if ref in indexed',ui)
        self.assertIn('remember_artwork(CONFIG_DIR',src('app.py'))


class UXContracts(unittest.TestCase):
    def test_close_keyboard_shortcuts_and_veto(self):
        self.assertTrue(is_close_shortcut('Escape',False))
        self.assertTrue(is_close_shortcut('w',True))
        self.assertTrue(is_close_shortcut('q',True))
        self.assertFalse(is_close_shortcut('w',False))
        self.assertFalse(is_close_shortcut('a',True))
        self.assertIn('window.close()  # honours close-request veto',src('window_shortcuts.py'))

    def test_preview_is_an_adw_application_window_with_title(self):
        ui=src('app.py')
        self.assertIn('class SaverWindow(Adw.ApplicationWindow)',ui)
        self.assertIn('self.set_title("ASCII Saver · Preview")',ui)
        self.assertIn('toolbar.add_top_bar(Adw.HeaderBar())',ui)
        self.assertIn('ctrl and name in ("w", "q")',ui)
        self.assertIn('not isinstance(_args[0], Gtk.EventControllerKey)',ui)

    def test_gallery_is_transient_and_centred(self):
        view=src('preferences_gallery_view.py')
        engine=src('preferences_gallery.py')
        self.assertIn('self.gallery_window = Adw.Window(',view)
        self.assertIn('transient_for=self, title="ASCII Saver · Effect library"',view)
        self.assertIn('install_close_shortcuts(self.gallery_window',view)
        self.assertIn('host.set_center_widget(terminal)',engine)
        self.assertIn('self.preview_area.set_child(host)',engine)
        self.assertIn('self.preview_area.set_child(None)',engine)

    def test_no_saved_banner_when_clean_and_wider_adaptation(self):
        shell=src('preferences_shell.py');state=src('preferences_state.py')
        self.assertIn('self.unsaved_banner.set_visible(False)',shell)
        self.assertIn('self.changes_tray.set_visible(is_dirty)',state)
        self.assertIn('min-width: 900sp',shell)
        self.assertIn('Gtk.Orientation.HORIZONTAL',shell)

    def test_dropdowns_fill_filter_width(self):
        for file in ('preferences_gallery_view.py','playlist_editor.py'):
            source=src(file)
            self.assertIn('center_string_dropdown(dropdown)',source)
        helper=src('adwaita_ui.py')
        self.assertIn('Gtk.SignalListItemFactory()',helper)
        self.assertIn('dropdown.set_factory(factory)',helper)
        self.assertIn('dropdown.set_list_factory(factory)',helper)
        self.assertIn('Gtk.Label(xalign=0.5, hexpand=True)',helper)

    def test_new_modules_are_in_install_manifest(self):
        install=src('install.sh')
        for name in ('palette_editor_model.py','artwork_selection.py',
                     'window_shortcuts.py','artwork_history.py'):
            self.assertIn(name,install)

    def test_all_modified_gtk_modules_parse_without_importing_gi(self):
        for f in ('app.py','preferences_controls.py','preferences_gallery.py',
                  'preferences_gallery_view.py','artwork_editor.py',
                  'artwork_library_view.py','artwork_online_view.py',
                  'artwork_canvas_view.py','preferences_state.py','preferences_shell.py'):
            with self.subTest(file=f): ast.parse(src(f))

if __name__=='__main__': unittest.main()
