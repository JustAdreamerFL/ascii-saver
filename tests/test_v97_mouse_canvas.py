"""V97 bounded mouse-driven ASCII canvas engine and editor wiring."""
from _bootstrap import SRC, read_source  # noqa: F401
from pathlib import Path
from types import SimpleNamespace
import ast
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from artwork_canvas import (CanvasShape, canvas_shape, line_cells, paint_stroke,
                            MAX_COLS, MAX_ROWS)


class CanvasEngineTests(unittest.TestCase):
    def test_default_size_and_exact_artwork_dimensions(self):
        self.assertEqual(canvas_shape(''), CanvasShape(48, 18))
        self.assertEqual(canvas_shape('hi\nxyz\n'), CanvasShape(48, 18))
        self.assertEqual(canvas_shape('a' * 90 + '\n' * 22), CanvasShape(90, 22))

    def test_bresenham_covers_every_rapid_mouse_cell(self):
        self.assertEqual(line_cells(1, 2, 6, 2), tuple((i, 2) for i in range(1, 7)))
        self.assertEqual(line_cells(1, 1, 5, 5), tuple((i, i) for i in range(1, 6)))
        self.assertEqual(line_cells(5, 5, 1, 1), tuple((i, i) for i in range(5, 0, -1)))
        for coords in ((0, 0, 9, 3), (9, 2, 0, 4), (3, 10, 4, 0)):
            cells = line_cells(*coords)
            self.assertEqual(cells[0], coords[:2])
            self.assertEqual(cells[-1], coords[2:])
            self.assertTrue(all(abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1
                                for a, b in zip(cells, cells[1:])))

    def test_paint_existing_and_blank_cells_preserves_original_line_endings(self):
        source = 'abc\nq\n'
        self.assertEqual(paint_stroke(source, ((0, 0), (2, 0)), '@'), '@b@\nq\n')
        self.assertEqual(paint_stroke(source, ((3, 1),), '#'), 'abc\nq  #\n')
        self.assertEqual(paint_stroke(source, ((1, 3),), '*'), 'abc\nq\n\n *\n')
        self.assertEqual(source, 'abc\nq\n')

    def test_eraser_clears_cells_without_growing_artwork(self):
        source = 'abc\nq\n'
        self.assertEqual(paint_stroke(source, ((1, 0),), '*', erase=True), 'a c\nq\n')
        self.assertEqual(paint_stroke(source, ((25, 15),), '*', erase=True), source)
        self.assertEqual(paint_stroke(source, ((2, 1),), '*', erase=True), source)
        self.assertEqual(paint_stroke(' ', ((0, 0),), '#', erase=True), ' ')

    def test_duplicate_stroke_cells_do_not_repeat_insertions(self):
        cells = ((2, 0), (2, 0), (0, 0), (2, 0), (0, 0))
        self.assertEqual(paint_stroke('a\n', cells, 'x'), 'x x\n')

    def test_missing_or_unsafe_characters_never_corrupt_data(self):
        for raw in ('漢字', 'a\u0301', '\t123', '\rfoo', '\x1b[31m', '\x00',
                    'a' * (MAX_COLS + 1), '\n' * (MAX_ROWS + 1)):
            with self.subTest(raw=repr(raw[:16])), self.assertRaises(ValueError):
                canvas_shape(raw)
        for cells in (((48, 0),), ((0, -1),), (('a', 0),), ((0, 0, 4),)):
            with self.subTest(cells=cells), self.assertRaises(ValueError):
                paint_stroke('a', cells, '#')
        for ink in ('é', '\t', 'two', '\x1b'):
            with self.subTest(ink=repr(ink)), self.assertRaises(ValueError):
                paint_stroke('a', ((0, 0),), ink)

    def test_single_column_unicode_box_art_remains_drawable(self):
        from pathlib import Path
        logo = (ROOT / 'config/logo.txt').read_text(encoding='utf-8')
        self.assertEqual(canvas_shape(logo), CanvasShape(48, 18))
        self.assertIn('╭', paint_stroke(logo, ((10, 2),), '#'))
        self.assertEqual(paint_stroke('café', ((0, 0),), '@'), '@afé')
        self.assertEqual(paint_stroke('│ ─ ╮', ((2, 0),), '*', erase=True), '│   ╮')

    def test_boundaries_and_large_but_supported_art(self):
        art = (' ' * MAX_COLS + '\n') * (MAX_ROWS - 1) + ' ' * MAX_COLS
        self.assertEqual(canvas_shape(art), CanvasShape(MAX_COLS, MAX_ROWS))
        self.assertEqual(paint_stroke(art, ((MAX_COLS - 1, MAX_ROWS - 1),), '@')[-1], '@')
        self.assertEqual(paint_stroke('', (), '@'), '')


class CanvasGtkSourceContracts(unittest.TestCase):
    def test_mouse_controller_renders_only_then_commits(self):
        view = (SRC / 'artwork_canvas_view.py').read_text(encoding='utf-8')
        ast.parse(view)
        for requirement in ('Gtk.GestureDrag()', "drag.connect('drag-begin'",
                            "drag.connect('drag-update'", "drag.connect('drag-end'",
                            'Gtk.EventControllerMotion()', 'line_cells(',
                            'paint_stroke(', 'self.on_commit(updated)', 'self.canvas.queue_draw()',
                            'PangoCairo.show_layout(', 'self._read_text()',
                            'self._stroke.clear()'):
            self.assertIn(requirement, view)
        self.assertNotIn('save_artwork', view)
        self.assertNotIn('set_text(updated)', view)

    def test_editor_reuses_one_buffer_and_groups_strokes_for_undo(self):
        source = (SRC / 'artwork_editor.py').read_text(encoding='utf-8')
        ast.parse(source)
        for phrase in ('Gtk.ToggleButton(label="Draw")',
                       'self.canvas_view = AsciiCanvas(',
                       'buffer,',
                       'self.editor_pages.add_named(scroller, "text")',
                       'self.editor_pages.add_named(self.canvas_view, "canvas")',
                       'buf.begin_user_action()', 'buf.end_user_action()',
                       'self.draw_mode.set_active(False)',
                       'self.canvas_controls.set_visible(False)',
                       'self.canvas_erase.get_active'):
            self.assertIn(phrase, source)
        method = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'ArtworkEditor'
                      for n in n.body if isinstance(n, ast.FunctionDef) and n.name == '_commit_canvas_stroke')
        body = ast.get_source_segment(source, method)
        self.assertNotIn('save_artwork', body)
        self.assertNotIn('.set_text(', body)
        self.assertIn('buf.delete(', body)
        self.assertIn('buf.insert(', body)

    def test_install_and_metadata_v97(self):
        install = (ROOT / 'install.sh').read_text()
        self.assertIn('artwork_canvas artwork_canvas_view', install)
        version = tuple(int(v) for v in (ROOT / 'VERSION').read_text().strip().split('.'))
        self.assertGreaterEqual(version, (0, 97, 0))
        self.assertIn('.'.join(str(v) for v in version),
                      (SRC / 'build_info.py').read_text())
        for name in ('ROADMAP.md', 'TASKS.md', 'CHANGELOG.md', 'MASTER-BACKLOG.md', 'RELEASE-V97.md'):
            self.assertIn('V97', read_source(name), name)


class _FakeIter:
    def __init__(self, n): self.n = n


class _FakeBuffer:
    def __init__(self, text):
        self.text = text
        self.actions = []
    def get_start_iter(self): return _FakeIter(0)
    def get_end_iter(self): return _FakeIter(len(self.text))
    def get_iter_at_offset(self, offset): return _FakeIter(offset)
    def begin_user_action(self): self.actions.append('begin')
    def end_user_action(self): self.actions.append('end')
    def delete(self, begin, end):
        self.text = self.text[:begin.n] + self.text[end.n:]
        self.actions.append('delete')
    def insert(self, start, text):
        self.text = self.text[:start.n] + text + self.text[start.n:]
        self.actions.append('insert')


class CanvasDirectBufferTests(unittest.TestCase):
    def test_actual_commit_edits_shared_buffer_once_without_file_write(self):
        source = (SRC / 'artwork_editor.py').read_text()
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'ArtworkEditor')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_commit_canvas_stroke')
        code = compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                       'artwork_editor.py', 'exec')
        namespace = {}
        exec(code, namespace)
        buffer = _FakeBuffer('original\n')
        host = SimpleNamespace(editor=SimpleNamespace(get_buffer=lambda: buffer), _text=lambda: buffer.text,
                               draw_mode=SimpleNamespace(get_active=lambda: False),
                               _canvas_commit_in_progress=False,
                               _canvas_text_changed=lambda: None)
        namespace['_commit_canvas_stroke'](host, 'new art\n')
        self.assertEqual(buffer.text, 'new art\n')
        self.assertEqual(buffer.actions, ['begin', 'delete', 'insert', 'end'])
        namespace['_commit_canvas_stroke'](host, 'new art\n')
        self.assertEqual(buffer.actions, ['begin', 'delete', 'insert', 'end'])

if __name__ == '__main__':
    unittest.main()

class CanvasDirectGestureTests(unittest.TestCase):
    """Exercise gesture callbacks without GTK with a deterministic fake canvas."""

    @staticmethod
    def methods():
        source = (SRC / 'artwork_canvas_view.py').read_text()
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'AsciiCanvas')
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)
                   and n.name in ('_drag_begin', '_drag_update', '_drag_end')]
        scope = {'line_cells': line_cells, 'paint_stroke': paint_stroke}
        from artwork_retouch import validate_ink
        scope['validate_ink'] = validate_ink
        exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])),
                     'artwork_canvas_view.py', 'exec'), scope)
        return scope

    @staticmethod
    def host(source, ink='#', erase=False):
        notices, commits, draws = [], [], []
        host = SimpleNamespace(
            text=source, shape=CanvasShape(48, 18), _stroke=set(), _stroke_origin=None,
            _previous_cell=None, _painting=False, keyboard_active=False,
            keyboard_cell=(0, 0),
            _notify_cell=lambda cell: None,
            _cell_at=lambda x, y: (int(x), int(y)) if 0 <= x < 48 and 0 <= y < 18 else None,
            is_erasing=lambda: erase,
            get_ink=lambda: ink,
            on_error=notices.append,
            canvas=SimpleNamespace(queue_draw=lambda: draws.append(True),
                                   grab_focus=lambda: None),
            _read_text=lambda: host.text,
        )
        def commit(text):
            commits.append(text)
            host.text = text
        host.on_commit = commit
        return host, commits, notices, draws

    def test_continuous_drag_commits_only_on_release(self):
        methods = self.methods()
        host, commits, notices, draws = self.host(' ' * 10 + '\n')
        host._drag_update = lambda _gesture, dx, dy: methods['_drag_update'](host, _gesture, dx, dy)
        methods['_drag_begin'](host, None, 0.1, 0.1)
        methods['_drag_update'](host, None, 7.0, 0.0)
        self.assertEqual(commits, [])
        self.assertEqual(host.text, ' ' * 10 + '\n')
        self.assertEqual(len(host._stroke), 8)
        methods['_drag_end'](host, None, 7.0, 0.0)
        self.assertEqual(commits, ['########  \n'])
        self.assertEqual(notices, [])
        self.assertFalse(host._stroke)
        self.assertFalse(host._painting)
        self.assertGreater(len(draws), 0)

    def test_invalid_ink_and_outside_press_are_noops(self):
        methods = self.methods()
        for ink, position, expected_notice in (('é', (1.0, 1.0), True),
                                               ('#', (-3.0, 1.0), False)):
            host, commits, notices, _ = self.host('abc\n', ink=ink)
            host._drag_update = lambda gesture, dx, dy: methods['_drag_update'](host, gesture, dx, dy)
            methods['_drag_begin'](host, None, *position)
            methods['_drag_end'](host, None, 5.0, 0.0)
            self.assertEqual(commits, [])
            self.assertEqual(bool(notices), expected_notice)
