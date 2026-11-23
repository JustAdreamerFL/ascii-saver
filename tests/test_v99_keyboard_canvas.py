"""V99 keyboard-accessible ASCII canvas, visible cursor and safe incremental edits."""
from _bootstrap import SRC, read_source  # noqa: F401
import ast
import math
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from artwork_canvas import (CanvasShape, KEYBOARD_DIRECTIONS, canvas_reveal_offset,
                            move_canvas_cursor, paint_stroke)


def source_methods(path, class_name, names, namespace):
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    cls = next(c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == class_name)
    methods = [m for m in cls.body if isinstance(m, ast.FunctionDef) and m.name in names]
    assert len(methods) == len(names)
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])), str(path), 'exec'), namespace)
    return namespace


class CanvasKeyboardMathTests(unittest.TestCase):
    def test_all_four_directions_and_edge_clamping(self):
        shape = CanvasShape(48, 18)
        self.assertEqual(set(KEYBOARD_DIRECTIONS), {'up', 'down', 'left', 'right'})
        self.assertEqual(move_canvas_cursor((0, 0), 'right', shape), (1, 0))
        self.assertEqual(move_canvas_cursor((1, 0), 'down', shape), (1, 1))
        self.assertEqual(move_canvas_cursor((0, 0), 'up', shape), (0, 0))
        self.assertEqual(move_canvas_cursor((0, 0), 'left', shape), (0, 0))
        self.assertEqual(move_canvas_cursor((47, 17), 'right', shape), (47, 17))
        self.assertEqual(move_canvas_cursor((47, 17), 'down', shape), (47, 17))

    def test_bad_coordinates_and_unknown_directions_are_rejected(self):
        for cell, direction in [((-1, 1), 'up'), ((48, 0), 'left'),
                                ((True, 1), 'right'), ((0, 0), 'diagonal')]:
            with self.subTest(cell=cell, direction=direction), self.assertRaises(ValueError):
                move_canvas_cursor(cell, direction, CanvasShape(48, 18))

    def test_ensure_cursor_visible_only_scrolls_when_necessary(self):
        self.assertEqual(canvas_reveal_offset(0, 100, 16, 10), 0)
        self.assertEqual(canvas_reveal_offset(30, 100, 70, 20), 30)
        self.assertEqual(canvas_reveal_offset(100, 100, 16, 10), 8)
        self.assertEqual(canvas_reveal_offset(0, 100, 98, 10), 16)
        self.assertEqual(canvas_reveal_offset(0, 8, 6, 10), 10)
        for args in [(-1, 50, 10, 10), (0, 0, 10, 10),
                     (0, 100, -1, 10), (0, 100, 10, 0), (0, float('nan'), 2, 10)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                canvas_reveal_offset(*args)


class _Adjustment:
    def __init__(self, page=60):
        self.value = 0
        self.page = page
        self.upper = 2000
    def get_value(self): return self.value
    def get_page_size(self): return self.page
    def get_lower(self): return 0
    def get_upper(self): return self.upper
    def set_value(self, value): self.value = value


class CanvasKeyboardWiringTests(unittest.TestCase):
    @staticmethod
    def methods():
        gdk = SimpleNamespace(ModifierType=SimpleNamespace(CONTROL_MASK=1, SHIFT_MASK=2,
                                                           ALT_MASK=4, SUPER_MASK=8),
                              keyval_name=lambda key: key)
        return source_methods(SRC / 'artwork_canvas_view.py', 'AsciiCanvas',
                              ('_key_pressed', '_notify_cell', '_paint_keyboard_cell',
                               '_reveal_keyboard_cell'),
                              {'Gdk': gdk, 'KEYBOARD_DIRECTIONS': KEYBOARD_DIRECTIONS,
                               'move_canvas_cursor': move_canvas_cursor,
                               'paint_stroke': paint_stroke,
                               'canvas_reveal_offset': canvas_reveal_offset})

    @staticmethod
    def fake_host(methods):
        commits, notices, positions, redraws = [], [], [], []
        h, v = _Adjustment(), _Adjustment()
        host = SimpleNamespace(shape=CanvasShape(48, 18), keyboard_cell=(0, 0),
                               keyboard_active=False, _painting=False, _zoom_serial=1, PAD=16,
                               cell_width=10, cell_height=20, text='abc\n',
                               get_ink=lambda: '#', on_error=notices.append,
                               on_position=positions.append,
                               on_undo=lambda: commits.append('undo'),
                               on_redo=lambda: commits.append('redo'),
                               get_hadjustment=lambda: h, get_vadjustment=lambda: v,
                               canvas=SimpleNamespace(queue_draw=lambda: redraws.append(1)))
        host._read_text = lambda: host.text
        def commit(value):
            commits.append(value)
            host.text = value
        host.on_commit = commit
        for name in ('_notify_cell', '_reveal_keyboard_cell', '_paint_keyboard_cell'):
            setattr(host, name, lambda *args, method=name, **kwargs:
                    methods[method](host, *args, **kwargs))
        return host, commits, notices, positions, redraws, h, v

    def test_keyboard_navigation_paint_erase_and_history(self):
        methods = self.methods()
        host, commits, notices, positions, redraws, h, v = self.fake_host(methods)
        key = lambda name, flags=0: methods['_key_pressed'](host, None, name, None, flags)
        self.assertTrue(key('KP_Right'))
        self.assertTrue(key('down'))
        self.assertEqual(host.keyboard_cell, (1, 1))
        self.assertEqual(host._zoom_serial, 3)
        self.assertEqual(positions[-1], (1, 1))
        self.assertTrue(key('space'))
        self.assertEqual(host.text, 'abc\n #\n')
        self.assertEqual(commits, ['abc\n #\n'])
        self.assertTrue(key('BackSpace'))
        self.assertEqual(host.text, 'abc\n  \n')
        self.assertTrue(key('delete'))
        self.assertEqual(len(commits), 2)  # no-op erase does not add history
        self.assertTrue(key('z', 1))
        self.assertTrue(key('z', 3))
        self.assertEqual(commits[-2:], ['undo', 'redo'])
        self.assertFalse(key('space', 2))   # shift+space is not intercepted
        self.assertFalse(key('Tab'))
        self.assertFalse(key('a', 1))
        self.assertEqual(notices, [])
        self.assertGreater(len(redraws), 0)

    def test_key_cursor_clamps_and_scrolls(self):
        methods = self.methods()
        host, commits, notices, positions, redraws, h, v = self.fake_host(methods)
        key = lambda name: methods['_key_pressed'](host, None, name, None, 0)
        for _ in range(80):
            key('right')
        self.assertEqual(host.keyboard_cell[0], 47)
        self.assertGreater(h.value, 0)
        for _ in range(40):
            key('down')
        self.assertEqual(host.keyboard_cell[1], 17)
        self.assertGreater(v.value, 0)
        self.assertFalse(key('escape'))  # do not hijack the normal close shortcut

    def test_unsupported_artwork_or_active_gesture_cannot_keyboard_paint(self):
        methods = self.methods()
        host, commits, notices, positions, redraws, h, v = self.fake_host(methods)
        host._painting = True
        methods['_paint_keyboard_cell'](host, erase=False)
        self.assertEqual(commits, [])
        host._painting = False
        host.shape = None
        self.assertFalse(methods['_key_pressed'](host, None, 'space', None, 0))
        self.assertEqual(commits, [])

    def test_editor_position_hint_and_safe_text_change_suppression(self):
        methods = source_methods(SRC / 'artwork_editor.py', 'ArtworkEditor',
                                 ('_canvas_position_changed', '_canvas_text_changed'), {})
        status = SimpleNamespace(text='', tooltip='',
                                 set_text=lambda v: setattr(status, 'text', v),
                                 get_text=lambda: status.text,
                                 set_tooltip_text=lambda v: setattr(status, 'tooltip', v))
        refreshes = []
        host = SimpleNamespace(canvas_hint=status, _canvas_commit_in_progress=True,
                               draw_mode=SimpleNamespace(get_active=lambda: True),
                               canvas_view=SimpleNamespace(refresh=lambda: refreshes.append(1) or True),
                               _sync_canvas_dimensions=lambda: None)
        methods['_canvas_position_changed'](host, (4, 8))
        self.assertIn('Cell 5, 9', status.text)
        self.assertIn('Space paints', status.tooltip)
        methods['_canvas_position_changed'](host, None)
        self.assertNotIn('Cell', status.text)
        methods['_canvas_text_changed'](host)
        self.assertEqual(refreshes, [])
        host._canvas_commit_in_progress = False
        methods['_canvas_text_changed'](host)
        self.assertEqual(refreshes, [1])


class _FakeBuffer:
    def __init__(self, text):
        self.text, self.events, self.on_changed = text, [], lambda: None
    def begin_user_action(self): self.events.append('begin')
    def end_user_action(self): self.events.append('end')
    def get_iter_at_offset(self, n): return n
    def delete(self, start, end):
        self.events.append(('delete', start, end))
        self.text = self.text[:start] + self.text[end:]
        self.on_changed()
    def insert(self, start, value):
        self.events.append(('insert', start, value))
        self.text = self.text[:start] + value + self.text[start:]
        self.on_changed()


class CanvasIncrementalBufferTests(unittest.TestCase):
    def test_partial_updates_do_not_refresh_incomplete_canvas_or_touch_other_lines(self):
        ns = source_methods(SRC / 'artwork_editor.py', 'ArtworkEditor',
                            ('_canvas_text_changed', '_commit_canvas_stroke'), {})
        fake = _FakeBuffer('abc\nhello\n')
        visible_refresh = []
        host = SimpleNamespace(editor=SimpleNamespace(get_buffer=lambda: fake),
                               _text=lambda: fake.text,
                               draw_mode=SimpleNamespace(get_active=lambda: True),
                               canvas_view=SimpleNamespace(refresh=lambda: visible_refresh.append(fake.text) or True),
                               _canvas_commit_in_progress=False,
                               _sync_canvas_dimensions=lambda: None)
        host._canvas_text_changed = lambda: ns['_canvas_text_changed'](host)
        fake.on_changed = host._canvas_text_changed
        ns['_commit_canvas_stroke'](host, 'a#c\nhello\n')
        self.assertEqual(fake.text, 'a#c\nhello\n')
        self.assertEqual(fake.events, ['begin', ('delete', 1, 2), ('insert', 1, '#'), 'end'])
        self.assertEqual(visible_refresh, ['a#c\nhello\n'])
        self.assertFalse(host._canvas_commit_in_progress)
        ns['_commit_canvas_stroke'](host, 'a#c\nhello\n')
        self.assertEqual(len(visible_refresh), 1)

    def test_append_only_and_erase_only_are_one_undo_action(self):
        ns = source_methods(SRC / 'artwork_editor.py', 'ArtworkEditor',
                            ('_canvas_text_changed', '_commit_canvas_stroke'), {})
        fake = _FakeBuffer('a\n')
        host = SimpleNamespace(editor=SimpleNamespace(get_buffer=lambda: fake),
                               _text=lambda: fake.text,
                               draw_mode=SimpleNamespace(get_active=lambda: False),
                               _canvas_commit_in_progress=False)
        host._canvas_text_changed = lambda: ns['_canvas_text_changed'](host)
        ns['_commit_canvas_stroke'](host, 'a\n  #')
        self.assertEqual(fake.text, 'a\n  #')
        self.assertEqual(fake.events, ['begin', ('insert', 2, '  #'), 'end'])
        fake.events.clear()
        ns['_commit_canvas_stroke'](host, 'a\n')
        self.assertEqual(fake.events, ['begin', ('delete', 2, 5), 'end'])
        self.assertEqual(fake.text, 'a\n')

    def test_version_and_source_integrations(self):
        editor = (SRC / 'artwork_editor.py').read_text()
        canvas = (SRC / 'artwork_canvas_view.py').read_text()
        self.assertIn('on_position=self._canvas_position_changed', editor)
        self.assertIn('self._canvas_commit_in_progress = True', editor)
        self.assertIn('self._canvas_commit_in_progress = False', editor)
        self.assertIn('self._reveal_keyboard_cell()', canvas)
        self.assertIn('self.keyboard_active = True', canvas)
        self.assertIn('self.on_commit(updated)', canvas)
        self.assertNotIn('save_artwork', canvas)
        self.assertGreaterEqual(tuple(map(int, (ROOT / 'VERSION').read_text().strip().split('.'))), (0, 99, 0))
        for document in ('ROADMAP.md', 'TASKS.md', 'CHANGELOG.md', 'RELEASE-V99.md'):
            self.assertIn('V99', read_source(document))


if __name__ == '__main__':
    unittest.main()
