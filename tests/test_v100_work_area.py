"""V100: non-destructive expandable work area and viewport-limited drawing."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401
import ast
import math
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from artwork_canvas import (CanvasShape, canvas_shape, paint_stroke,
                            visible_cell_range, validate_workspace, canvas_cell_at)


def method_source(filename, cls, names, scope):
    text = read_source(filename)
    tree = ast.parse(text)
    klass = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == cls)
    methods = [node for node in klass.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(methods) == len(names)
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])), filename, 'exec'), scope)
    return scope


class WorkspaceModelTests(unittest.TestCase):
    def test_work_area_expands_without_inserting_any_text(self):
        source = '  /\\\n (  )\n'
        self.assertEqual(canvas_shape(source), CanvasShape(48, 18))
        self.assertEqual(canvas_shape(source, CanvasShape(120, 70)), CanvasShape(120, 70))
        self.assertEqual(source, '  /\\\n (  )\n')
        result = paint_stroke(source, ((119, 69),), '#', workspace=CanvasShape(120, 70))
        self.assertEqual(result.splitlines()[69][-1], '#')
        self.assertEqual(canvas_shape(result), CanvasShape(120, 70))
        self.assertEqual(result.splitlines()[:2], source.splitlines())

    def test_erase_empty_workspace_never_grows_artwork(self):
        original = 'HELLO\n'
        workspace = CanvasShape(200, 100)
        self.assertEqual(paint_stroke(original, ((199, 99),), '@', erase=True,
                                      workspace=workspace), original)
        self.assertEqual(paint_stroke(original, ((1, 0),), '@', erase=True,
                                      workspace=workspace), 'H LLO\n')

    def test_workspace_smaller_than_existing_art_cannot_crop(self):
        original = 'H' * 170 + '\n' * 90
        shape = canvas_shape(original, CanvasShape(48, 18))
        self.assertEqual(shape, CanvasShape(170, 90))
        self.assertEqual(paint_stroke(original, ((169, 89),), '#',
                                      workspace=CanvasShape(48, 18)).splitlines()[-1][-1], '#')

    def test_workspace_input_is_strictly_bounded(self):
        for shape in [CanvasShape(47, 18), CanvasShape(201, 18), CanvasShape(48, 17),
                      CanvasShape(48, 101), CanvasShape(True, 18), CanvasShape(48.0, 18),
                      (48, 18), None]:
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                validate_workspace(shape)
        with self.assertRaises(ValueError):
            paint_stroke('hi', ((130, 20),), '#')  # still bounded by default
        self.assertEqual(validate_workspace(CanvasShape(48, 18)), CanvasShape(48, 18))
        self.assertEqual(validate_workspace(CanvasShape(200, 100)), CanvasShape(200, 100))

    def test_unicode_one_cell_art_can_extend_safely(self):
        shape = canvas_shape('café', CanvasShape(200, 100))
        self.assertEqual(shape, CanvasShape(200, 100))
        painted = paint_stroke('│ café', ((50, 5),), '#', workspace=shape)
        self.assertIn('│ café', painted)
        self.assertEqual(painted.splitlines()[5][50], '#')
        for unsafe in ('漢', 'a\u0301', 'a\t'):
            with self.subTest(unsafe=repr(unsafe)), self.assertRaises(ValueError):
                canvas_shape(unsafe, shape)

    def test_pointer_math_stays_correct_for_expanded_area(self):
        shape = CanvasShape(200, 100)
        self.assertEqual(canvas_cell_at(16 + 199.5 * 12, 16 + 99.5 * 25,
                                        shape, 12, 25), (199, 99))
        self.assertIsNone(canvas_cell_at(16 + 200 * 12, 16, shape, 12, 25))


class VisibleRangeTests(unittest.TestCase):
    def test_visible_subrange_for_small_and_large_viewport(self):
        self.assertEqual(visible_cell_range(0, 80, 10, 200), (0, 8))
        self.assertEqual(visible_cell_range(16 + 55 * 10, 90, 10, 200), (54, 65))
        self.assertEqual(visible_cell_range(16 + 198 * 10, 180, 10, 200), (197, 200))
        self.assertEqual(visible_cell_range(0, 0, 10, 200), (0, 200))
        self.assertEqual(visible_cell_range(100000, 100, 10, 200), (200, 200))

    def test_visible_range_rejects_invalid_viewports(self):
        for args in ((-1, 200, 10, 200), (0, -1, 10, 200),
                     (0, 200, 0, 200), (0, 200, 10, -1),
                     (math.nan, 100, 10, 200), (0, math.inf, 10, 200)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                visible_cell_range(*args)


class WorkspaceUIContracts(unittest.TestCase):
    def test_workspace_view_ops_never_change_text(self):
        scope = method_source('artwork_canvas_view.py', 'AsciiCanvas',
                              ('set_workspace', 'fit_workspace'),
                              {'CanvasShape': CanvasShape, 'validate_workspace': validate_workspace,
                               'canvas_shape': canvas_shape})
        source = 'abc\n' + 'x' * 110
        events = []
        host = SimpleNamespace(workspace=CanvasShape(48, 18), text=source,
                               cancel_stroke=lambda: events.append('cancel'),
                               refresh=lambda: events.append('refresh'),
                               _read_text=lambda: source)
        host.set_workspace = lambda w, h: scope['set_workspace'](host, w, h)
        self.assertEqual(host.set_workspace(150, 80), CanvasShape(150, 80))
        self.assertEqual(host.workspace, CanvasShape(150, 80))
        self.assertEqual(scope['fit_workspace'](host), CanvasShape(110, 18))
        self.assertEqual(host.workspace, CanvasShape(48, 18))
        self.assertEqual(host.text, source)
        self.assertEqual(events, ['cancel', 'refresh', 'cancel', 'refresh'])
        with self.assertRaises(ValueError):
            host.set_workspace(201, 80)
        self.assertEqual(host.workspace, CanvasShape(48, 18))

    def test_draw_only_lays_out_text_near_viewport(self):
        shown = []
        class FakeLayout:
            def __init__(self): self.text = ''
            def set_font_description(self, desc): pass
            def set_text(self, text): self.text = text
        class FakeCairo:
            def __getattr__(self, name):
                if name in ('set_source_rgb','paint','set_line_width','move_to',
                            'line_to','stroke','set_source_rgba','rectangle','fill'):
                    return lambda *args: None
                raise AttributeError(name)
        scope = method_source('artwork_canvas_view.py', 'AsciiCanvas', ('_draw',), {
            'Adw': SimpleNamespace(StyleManager=SimpleNamespace(
                get_default=lambda: SimpleNamespace(get_dark=lambda: False))),
            'visible_cell_range': visible_cell_range,
            'PangoCairo': SimpleNamespace(show_layout=lambda _cr, layout: shown.append(layout.text)),
        })
        text = '\n'.join(('x' * 180) for _ in range(100))
        host = SimpleNamespace(shape=CanvasShape(180, 100), PAD=16, cell_width=10,
                               cell_height=20, show_grid=True,
                               _font_description=object(), _painting=False,
                               _stroke=set(), hover=None, keyboard_active=False,
                               get_hadjustment=lambda: SimpleNamespace(get_value=lambda: 16 + 70 * 10,
                                                                       get_page_size=lambda: 100),
                               get_vadjustment=lambda: SimpleNamespace(get_value=lambda: 16 + 80 * 20,
                                                                       get_page_size=lambda: 80),
                               _read_text=lambda: text)
        area = SimpleNamespace(create_pango_layout=lambda _: FakeLayout())
        scope['_draw'](host, area, FakeCairo(), 1800, 2000)
        self.assertGreater(len(shown), 0)
        self.assertLessEqual(len(shown), 7)
        self.assertTrue(all(len(line) <= 13 for line in shown))
        self.assertTrue(all('x' == char for line in shown for char in line))

    def test_existing_artwork_dimensions_appear_in_popover(self):
        scope = method_source('artwork_editor.py', 'ArtworkEditor',
                              ('_sync_canvas_dimensions',), {})
        measured = []
        host = SimpleNamespace(canvas_view=SimpleNamespace(shape=CanvasShape(182, 82)),
                               canvas_columns=SimpleNamespace(
                                   set_value=lambda v: measured.append(('cols', v))),
                               canvas_rows=SimpleNamespace(
                                   set_value=lambda v: measured.append(('rows', v))))
        scope['_sync_canvas_dimensions'](host)
        self.assertEqual(measured, [('cols', 182), ('rows', 82)])
        host.canvas_view.shape = None
        scope['_sync_canvas_dimensions'](host)
        self.assertEqual(len(measured), 2)

    def test_editor_work_area_is_a_real_advanced_popover(self):
        editor = (SRC / 'artwork_editor.py').read_text()
        canvas = (SRC / 'artwork_canvas_view.py').read_text()
        for item in ('Gtk.MenuButton(label="Work area")',
                     'Gtk.SpinButton.new_with_range(48, 200, 1)',
                     'Gtk.SpinButton.new_with_range(18, 100, 1)',
                     'self.canvas_view.set_workspace(',
                     'self.canvas_view.fit_workspace(',
                     'workspace_popover.set_child(workspace_panel)'):
            self.assertIn(item, editor)
        self.assertIn('workspace=self.shape', canvas)
        self.assertIn('visible_cell_range(', canvas)
        self.assertNotIn('save_artwork', canvas)
        self.assertGreaterEqual(tuple(map(int, (ROOT / 'VERSION').read_text().strip().split('.'))), (0, 100, 0))
        self.assertTrue((ROOT / 'docs/releases/RELEASE-V100.md').is_file())


if __name__ == '__main__':
    unittest.main()
