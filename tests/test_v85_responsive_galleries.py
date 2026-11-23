"""V85: narrow-window UX and filtering must not alter saved selections.

These tests run without GTK. Actual breakpoints/window allocation still need
interactive verification on GNOME and KDE Wayland.
"""
import ast
from pathlib import Path
import types
import unittest

from effect_catalog import EFFECTS
from effect_library import select_effects

ROOT = Path(__file__).resolve().parents[1]


def method(filename, class_name, function):
    tree = ast.parse((ROOT / filename).read_text(encoding='utf-8'))
    klass = next(c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == class_name)
    fn = next(f for f in klass.body if isinstance(f, ast.FunctionDef) and f.name == function)
    mod = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    env = {'EFFECTS': EFFECTS, 'select_effects': select_effects}
    exec(compile(mod, filename, 'exec'), env)
    return env[function]


class FakeFilter:
    def __init__(self, value='', selected=0, changed=None):
        self.value, self.selected, self.changed = value, selected, changed

    def get_text(self): return self.value
    def get_selected(self): return self.selected
    def set_text(self, value):
        self.value = value
        if self.changed: self.changed()
    def set_selected(self, value):
        self.selected = value
        if self.changed: self.changed()


class FakeFlowBox:
    def __init__(self):
        self.children = []
        self.insertions = 0

    def insert(self, card, position):
        self.children.append(types.SimpleNamespace(card=card))
        self.insertions += 1

    def get_first_child(self):
        return self.children[0] if self.children else None

    def remove(self, wrapper):
        self.children.remove(wrapper)

    def names(self):
        return [child.card for child in self.children]


class ResponsiveGalleryTests(unittest.TestCase):
    def test_effect_library_flowbox_adapts_and_keeps_scroll_region(self):
        source = (ROOT / 'preferences_gallery_view.py').read_text()
        self.assertIn('effect_grid = Gtk.FlowBox()', source)
        self.assertIn('effect_grid.set_min_children_per_line(1)', source)
        self.assertIn('effect_grid.set_max_children_per_line(3)', source)
        self.assertNotIn('effect_grid = Gtk.Grid(', source)
        self.assertIn('gallery_scroll.set_child(effect_grid)', source)
        self.assertIn('gallery_shell.append(self.gallery_stack)', source)
        self.assertIn('gallery_shell.append(self.live_preview_revealer)', source)
        self.assertLess(source.index('gallery_shell.append(self.gallery_stack)'),
                        source.index('gallery_shell.append(self.live_preview_revealer)'))

    def test_both_filter_toolbars_reflow_before_window_is_too_small(self):
        library = (ROOT / 'preferences_gallery_view.py').read_text()
        editor = (ROOT / 'playlist_editor.py').read_text()
        self.assertIn('compact.add_setter(library_toolbar, "orientation", Gtk.Orientation.VERTICAL)', library)
        self.assertIn('compact.add_setter(preview_mode_row, "orientation", Gtk.Orientation.VERTICAL)', library)
        self.assertIn('smallest.add_setter(library_actions, "orientation", Gtk.Orientation.VERTICAL)', library)
        self.assertIn('self.gallery_window.add_breakpoint(compact)', library)
        self.assertIn('narrow.add_setter(filters, "orientation", Gtk.Orientation.VERTICAL)', editor)
        self.assertIn('narrow.add_setter(columns, "collapsed", True)', editor)

    def test_filters_preserve_card_identity_order_and_empty_result(self):
        run = method('preferences_gallery.py', 'GalleryControllerMixin', '_filter_effect_library')
        boxes = FakeFlowBox()
        saved_cards = {name: object() for name in EFFECTS}
        summary = types.SimpleNamespace(value='', set_text=lambda s: setattr(summary, 'value', s))
        view = types.SimpleNamespace(visible='gallery',
                                     set_visible_child_name=lambda name: setattr(view, 'visible', name))
        refreshes = []
        host = types.SimpleNamespace(
            library_grid=boxes, effect_cells=saved_cards,
            library_search=FakeFilter(value='RAIN'),
            library_duration=FakeFilter(selected=0),
            library_intensity=FakeFilter(selected=0),
            library_count=summary, gallery_stack=view,
            gallery_scroll=object(), _queue_gallery_sync=lambda: refreshes.append(True),
        )
        # Saved choices are not touched, even when cards leave the layout.
        original_cards = dict(host.effect_cells)
        run(host)
        self.assertEqual(boxes.names(), [saved_cards['rain']])
        self.assertEqual(view.visible, 'gallery')
        self.assertIn('1 of 37', summary.value)
        host.library_search.value = 'this effect does not exist'
        run(host)
        self.assertEqual(boxes.names(), [])
        self.assertEqual(view.visible, 'empty')
        self.assertEqual(host.effect_cells, original_cards)
        host.library_search.value = ''
        run(host)
        self.assertEqual(boxes.names(), [saved_cards[name] for name in EFFECTS])
        self.assertEqual(len(refreshes), 3)

    def test_library_clear_filters_rebuilds_once_and_does_not_write_config(self):
        run = method('preferences_gallery.py', 'GalleryControllerMixin', '_filter_effect_library')
        clear = method('preferences_gallery.py', 'GalleryControllerMixin', '_clear_library_filters')
        boxes = FakeFlowBox()
        view = types.SimpleNamespace(set_visible_child_name=lambda _: None)
        summary = types.SimpleNamespace(set_text=lambda _: None)
        refreshes = []
        host = types.SimpleNamespace(library_grid=boxes,
                                     effect_cells={name: object() for name in EFFECTS},
                                     library_search=FakeFilter(value='rain'),
                                     library_duration=FakeFilter(selected=1),
                                     library_intensity=FakeFilter(selected=2),
                                     library_count=summary, gallery_stack=view,
                                     gallery_scroll=object(),
                                     _queue_gallery_sync=lambda: refreshes.append('refresh'))
        host._filter_effect_library = lambda: run(host)
        for field in (host.library_search, host.library_duration, host.library_intensity):
            field.changed = host._filter_effect_library
        clear(host)
        self.assertEqual(len(refreshes), 1)
        self.assertEqual(len(boxes.names()), len(EFFECTS))
        self.assertEqual(host.library_search.get_text(), '')
        self.assertEqual(host.library_duration.get_selected(), 0)
        self.assertEqual(host.library_intensity.get_selected(), 0)

    def test_playlist_empty_search_has_a_single_reset_and_no_playlist_edit(self):
        source = (ROOT / 'playlist_editor.py').read_text()
        self.assertIn("clear_filters.connect('clicked', self._clear_effect_filters)", source)
        self.assertIn("self.gallery_stack.add_named(empty, 'empty')", source)
        self.assertIn("self._filter_update_suspended = True", source)
        self.assertIn("if getattr(self, '_filter_update_suspended', False):", source)
        reset = method('playlist_editor.py', 'Editor', '_clear_effect_filters')
        count = []
        host = types.SimpleNamespace(search=FakeFilter(value='rain'),
                                     duration=FakeFilter(selected=2),
                                     intensity=FakeFilter(selected=3),
                                     refresh_effects=lambda: count.append('refresh'))
        # If filter signals still fire, they are blocked during the clear.
        for control in (host.search, host.duration, host.intensity):
            control.changed = lambda: count.append('signal') if not getattr(host, '_filter_update_suspended', False) else None
        reset(host)
        self.assertEqual(count, ['refresh'])
        self.assertEqual((host.search.get_text(), host.duration.get_selected(), host.intensity.get_selected()),
                         ('', 0, 0))

    def test_release_remains_explicitly_runtime_unverified(self):
        self.assertGreaterEqual(tuple(map(int, (ROOT / 'VERSION').read_text().strip().split('.'))), (0, 85, 0))
        self.assertIn('## 0.85.0 (experimental) - 2026-11-08',
                      (ROOT / 'CHANGELOG.md').read_text())
        self.assertIn('not verified', (ROOT / 'RELEASE-V85.md').read_text())


if __name__ == '__main__':
    unittest.main()
