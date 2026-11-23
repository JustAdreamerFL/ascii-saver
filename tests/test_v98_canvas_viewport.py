"""V98 canvas zoom, logical coordinates, keyboard focus and stable viewport."""
import ast
import math
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from artwork_canvas import (CanvasShape, canvas_cell_at, zoom_scroll_offset,
                            ZOOM_LEVELS, paint_stroke)


class ViewportGeometryTests(unittest.TestCase):
    def test_zoom_choices_are_bounded_and_include_original(self):
        self.assertEqual(ZOOM_LEVELS, (75, 100, 125, 150, 200))

    def test_pointer_coordinates_map_to_exact_cells_without_double_scaling(self):
        shape = CanvasShape(48, 18)
        for cw, ch in ((8, 16), (12, 24), (18, 36), (25, 47)):
            for col, row in ((0, 0), (4, 3), (47, 17)):
                x, y = 16 + cw * (col + 0.5), 16 + ch * (row + 0.5)
                self.assertEqual(canvas_cell_at(x, y, shape, cw, ch), (col, row))
            self.assertEqual(canvas_cell_at(16 + cw, 16, shape, cw, ch), (1, 0))
            self.assertEqual(canvas_cell_at(15.999, 16, shape, cw, ch), None)
            self.assertEqual(canvas_cell_at(16, 15.999, shape, cw, ch), None)
            self.assertEqual(canvas_cell_at(16 + 48 * cw, 16, shape, cw, ch), None)
            self.assertEqual(canvas_cell_at(16, 16 + 18 * ch, shape, cw, ch), None)

    def test_nonfinite_coordinates_and_invalid_cell_sizes(self):
        shape = CanvasShape(48, 18)
        for coord in ((math.nan, 1), (math.inf, 0), (0, -math.inf)):
            self.assertIsNone(canvas_cell_at(*coord, shape, 11, 20))
        with self.assertRaises(ValueError):
            canvas_cell_at(0, 0, shape, 0, 20)

    def test_preserve_visible_logical_cell_during_zoom(self):
        for old, new in ((10, 18), (18, 10), (14, 14)):
            self.assertEqual(zoom_scroll_offset(0, old, new), 0)
            self.assertEqual(zoom_scroll_offset(8, old, new), 8)
            position = 16 + 28.5 * old
            rescaled = zoom_scroll_offset(position, old, new)
            self.assertAlmostEqual((rescaled - 16) / new, 28.5)
        with self.assertRaises(ValueError):
            zoom_scroll_offset(-1, 10, 11)

    def test_viewport_changes_never_touch_ascii_text(self):
        art = '  /\\\n (  )\n  \\/\n'
        for cell in ((0, 0), (2, 1), (47, 17)):
            pos = canvas_cell_at(16 + 18 * (cell[0] + .5),
                                 16 + 35 * (cell[1] + .5), CanvasShape(48, 18), 18, 35)
            self.assertEqual(pos, cell)
        self.assertEqual(art, '  /\\\n (  )\n  \\/\n')
        self.assertIn('#', paint_stroke(art, ((1, 1),), '#'))


class _Adjustment:
    def __init__(self, value, upper=4000, page_size=350):
        self.value, self.upper, self.page_size = value, upper, page_size
    def get_value(self): return self.value
    def get_lower(self): return 0
    def get_upper(self): return self.upper
    def get_page_size(self): return self.page_size
    def set_value(self, value): self.value = value


def source_methods(path, cls_name, method_names, namespace):
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    cls = next(c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == cls_name)
    methods = [m for m in cls.body if isinstance(m, ast.FunctionDef) and m.name in method_names]
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])),
                 str(path), 'exec'), namespace)
    return namespace


class CanvasViewBehaviorTests(unittest.TestCase):
    def test_zoom_cancels_pending_stroke_and_preserves_viewport(self):
        callbacks, draws = [], []
        namespace = source_methods(ROOT / 'artwork_canvas_view.py', 'AsciiCanvas',
                                   ('cancel_stroke', 'set_zoom', '_restore_scroll_after_zoom'),
                                   {'ZOOM_LEVELS': ZOOM_LEVELS,
                                    'zoom_scroll_offset': zoom_scroll_offset,
                                    'GLib': SimpleNamespace(idle_add=lambda *args: callbacks.append(args))})
        h, v = _Adjustment(16 + 30 * 10), _Adjustment(16 + 12 * 20)
        host = SimpleNamespace(zoom=100, cell_width=10, cell_height=20,
                               _zoom_serial=0, PAD=16, _stroke={(2, 3)},
                               _stroke_origin=(22, 60), _previous_cell=(2, 3),
                               _painting=True,
                               canvas=SimpleNamespace(queue_draw=lambda: draws.append(True)),
                               get_hadjustment=lambda: h, get_vadjustment=lambda: v)
        host.cancel_stroke = lambda: namespace['cancel_stroke'](host)
        host._restore_scroll_after_zoom = lambda serial, x, y: namespace['_restore_scroll_after_zoom'](host, serial, x, y)
        def refresh():
            host.cell_width, host.cell_height = 20, 40
            return True
        host.refresh = refresh
        namespace['set_zoom'](host, 200)
        self.assertEqual(host.zoom, 200)
        self.assertFalse(host._painting)
        self.assertFalse(host._stroke)
        self.assertTrue(draws)
        callback, serial, wanted_x, wanted_y = callbacks.pop()
        self.assertEqual(serial, 1)
        self.assertAlmostEqual(wanted_x, 16 + 30 * 20)
        self.assertAlmostEqual(wanted_y, 16 + 12 * 40)
        callback(serial, wanted_x, wanted_y)
        self.assertEqual(h.value, 16 + 30 * 20)
        self.assertEqual(v.value, 16 + 12 * 40)
        with self.assertRaises(ValueError):
            namespace['set_zoom'](host, 300)

    def test_stale_zoom_scroll_callback_is_rejected_and_clamped(self):
        namespace = source_methods(ROOT / 'artwork_canvas_view.py', 'AsciiCanvas',
                                   ('_restore_scroll_after_zoom',), {})
        h = _Adjustment(10, upper=90, page_size=40)
        v = _Adjustment(10, upper=60, page_size=60)
        host = SimpleNamespace(_zoom_serial=2, get_hadjustment=lambda: h,
                               get_vadjustment=lambda: v)
        self.assertFalse(namespace['_restore_scroll_after_zoom'](host, 1, 500, 500))
        self.assertEqual(h.value, 10)
        self.assertFalse(namespace['_restore_scroll_after_zoom'](host, 2, 500, 500))
        self.assertEqual(h.value, 50)
        self.assertEqual(v.value, 0)

    def test_canvas_keyboard_shortcuts_do_not_switch_to_text_mode(self):
        namespace = source_methods(ROOT / 'artwork_canvas_view.py', 'AsciiCanvas',
                                   ('_key_pressed',), {
                                       'Gdk': SimpleNamespace(
                                           ModifierType=SimpleNamespace(CONTROL_MASK=1, SHIFT_MASK=2),
                                           keyval_name=lambda key: key)})
        actions = []
        host = SimpleNamespace(on_undo=lambda: actions.append('undo'),
                               on_redo=lambda: actions.append('redo'), shape=None)
        callback = namespace['_key_pressed']
        self.assertTrue(callback(host, None, 'z', None, 1))
        self.assertTrue(callback(host, None, 'Z', None, 3))
        self.assertTrue(callback(host, None, 'y', None, 1))
        self.assertFalse(callback(host, None, 'a', None, 1))
        self.assertFalse(callback(host, None, 'z', None, 0))
        self.assertEqual(actions, ['undo', 'redo', 'redo'])

    def test_editor_restores_focus_to_active_mode(self):
        namespace = source_methods(ROOT / 'artwork_editor.py', 'ArtworkEditor',
                                   ('_restore_editing_focus',), {})
        focus = []
        host = SimpleNamespace(draw_mode=SimpleNamespace(get_active=lambda: True),
                               canvas_view=SimpleNamespace(canvas=SimpleNamespace(
                                   grab_focus=lambda: focus.append('canvas'))),
                               editor=SimpleNamespace(grab_focus=lambda: focus.append('text')))
        namespace['_restore_editing_focus'](host)
        host.draw_mode = SimpleNamespace(get_active=lambda: False)
        namespace['_restore_editing_focus'](host)
        self.assertEqual(focus, ['canvas', 'text'])

    def test_wiring_contracts_responsive_and_safe(self):
        editor = (ROOT / 'artwork_editor.py').read_text()
        view = (ROOT / 'artwork_canvas_view.py').read_text()
        for snippet in ('Gtk.FlowBox()', 'Gtk.DropDown.new_from_strings(',
                        'Gtk.CheckButton(label="Grid")', 'self.canvas_view.set_zoom(',
                        'self.canvas_view.set_grid_visible(',
                        'self.canvas_view.cancel_stroke()',
                        'self.canvas_view.canvas.grab_focus()'):
            self.assertIn(snippet, editor)
        for snippet in ('Gtk.EventControllerKey()', 'keys.connect(\'key-pressed\'',
                        'self.canvas.set_focusable(True)',
                        'layout.set_font_description(self._font_description)',
                        'canvas_cell_at(', 'GLib.idle_add(',
                        'self._zoom_serial', 'if self.show_grid:'):
            self.assertIn(snippet, view)
        self.assertNotIn('save_artwork', view)


if __name__ == '__main__':
    unittest.main()
