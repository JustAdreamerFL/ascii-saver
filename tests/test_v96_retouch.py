"""V96 manual artwork retouch: pure transforms and direct buffer edit contracts."""
from __future__ import annotations

import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest

from artwork_editor_io import read_artwork, save_artwork
from artwork_retouch import (MAX_SELECTION, validate_ink, paint_at, paint_selection,
                            mirror_selection, flip_selection)

ROOT = Path(__file__).resolve().parents[1]


class RetouchEngineTests(unittest.TestCase):
    def test_ink_is_one_printable_ascii_character(self):
        for glyph in ('@', '.', ' ', '\\', '|', '~', '#'):
            self.assertEqual(validate_ink(glyph), glyph)
        for glyph in ('', '\n', '\t', '\x1b', 'é', '界', 'aa', 1, None):
            with self.subTest(glyph=glyph), self.assertRaises(ValueError):
                validate_ink(glyph)

    def test_paint_overwrites_cell_and_moves_caret_one_character(self):
        text = ' /\\\n<=>\n'
        result, pos = paint_at(text, 1, '@')
        self.assertEqual(result, ' @\\\n<=>\n')
        self.assertEqual(pos, 2)
        self.assertEqual(text, ' /\\\n<=>\n')

    def test_paint_at_line_end_inserts_not_overwrites_newline(self):
        self.assertEqual(paint_at('ab\ncd', 2, '*'), ('ab*\ncd', 3))
        self.assertEqual(paint_at('ab\n', 3, '*'), ('ab\n*', 4))
        self.assertEqual(paint_at('', 0, '#'), ('#', 1))
        self.assertEqual(paint_at('hi', 2, '!'), ('hi!', 3))

    def test_erase_never_extends_artwork(self):
        self.assertEqual(paint_at('abc\nx', 1, '#', erase=True), ('a c\nx', 2))
        self.assertEqual(paint_at('ab\n', 2, '#', erase=True), ('ab\n', 2))
        self.assertEqual(paint_at('ab\n', 3, '#', erase=True), ('ab\n', 3))
        self.assertEqual(paint_at('', 0, '#', erase=True), ('', 0))

    def test_invalid_offsets_never_mutate(self):
        for pos in (-1, 4, 100, None, '1'):
            with self.subTest(pos=pos), self.assertRaises(ValueError):
                paint_at('abc', pos, '#')

    def test_horizontal_mirror_reverses_directional_brackets_and_slashes(self):
        self.assertEqual(mirror_selection('/>\n (['), ' <\\\n]) ')
        self.assertEqual(mirror_selection('()[]{}<>/\\'), '/\\<>{}[]()')
        self.assertEqual(mirror_selection('  /\n<'), '\\  \n  >')
        self.assertEqual(mirror_selection('/>\n ([' + '\n'), ' <\\\n]) ' + '\n')

    def test_vertical_flip_keeps_line_terminator_and_spaces(self):
        self.assertEqual(flip_selection('ab \n c\n'), ' c\nab \n')
        self.assertEqual(flip_selection('ab \n c'), ' c\nab ')
        self.assertEqual(flip_selection('single'), 'single')
        self.assertEqual(flip_selection(''), '')

    def test_selection_limits_prevent_giant_undo_buffer(self):
        self.assertEqual(MAX_SELECTION, 200_000)
        for text in ('a' * (MAX_SELECTION + 1), '\r', '\x00'):
            with self.assertRaises(ValueError):
                mirror_selection(text)
        self.assertEqual(flip_selection('x' * MAX_SELECTION), 'x' * MAX_SELECTION)

    def test_file_is_untouched_until_explicit_save(self):
        with TemporaryDirectory() as folder:
            art = Path(folder) / 'original.txt'
            art.write_text('(/\n)', encoding='utf-8')
            result, _ = paint_at(read_artwork(art), 0, '#')
            self.assertEqual(read_artwork(art), '(/\n)')
            save_artwork(art, result)
            self.assertEqual(read_artwork(art), '#/\n)')


class RetouchUIContracts(unittest.TestCase):
    def test_gtk_menu_has_explicit_tools_and_native_undo(self):
        source = (ROOT / 'artwork_editor.py').read_text(encoding='utf8')
        ast.parse(source)
        for required in (
            'Gtk.MenuButton(label="Retouch")',
            'paint.connect("clicked", self._paint_ink)',
            'erase.connect("clicked", self._erase_ink)',
            'self._transform_selection(mirror_selection)',
            'self._transform_selection(flip_selection)',
            'buffer.set_enable_undo(True)',
            'buffer.set_max_undo_levels(80)',
            'buf.begin_user_action()',
            'buf.end_user_action()',
            'buf.get_can_undo()',
            'buf.get_can_redo()',
            'buf.undo()', 'buf.redo()',
            'if buf.get_has_selection():',
            'if transformed == original:',
            'if self._text() != self.original_text and not self._close_confirmed:',
        ):
            self.assertIn(required, source)
        # Retouch controls manipulate only the in-memory GtkTextBuffer.
        for name in ('_paint_cell', '_transform_selection', '_undo_edit', '_redo_edit'):
            method = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name=='ArtworkEditor'
                          for n in n.body if isinstance(n, ast.FunctionDef) and n.name==name)
            self.assertNotIn('save_artwork', ast.get_source_segment(source, method))

    def test_installer_and_documentation_reflect_v96(self):
        self.assertTrue(all(module in (ROOT / 'install.sh').read_text() for module in ('artwork_editor_io', 'artwork_retouch', 'artwork_templates')))
        self.assertGreaterEqual(tuple(map(int, (ROOT / 'VERSION').read_text().strip().split('.'))), (0, 96, 0))
        self.assertIn((ROOT / 'VERSION').read_text().strip(), (ROOT / 'build_info.py').read_text())
        for name in ('ROADMAP.md', 'TASKS.md', 'CHANGELOG.md', 'MASTER-BACKLOG.md', 'RELEASE-V96.md'):
            self.assertIn('V96', (ROOT / name).read_text(), name)


if __name__ == '__main__':
    unittest.main()


class _FakeIter:
    def __init__(self, position):
        self.position = position

    def get_offset(self):
        return self.position


class _FakeBuffer:
    def __init__(self, text, caret=0, selection=None):
        self.text = text
        self.caret = caret
        self.selection = selection
        self.events = []

    def get_has_selection(self):
        return bool(self.selection and self.selection[0] != self.selection[1])

    def get_insert(self):
        return object()

    def get_iter_at_mark(self, _mark):
        return _FakeIter(self.caret)

    def get_iter_at_offset(self, offset):
        return _FakeIter(offset)

    def get_selection_bounds(self):
        assert self.get_has_selection()
        start, end = self.selection
        return True, _FakeIter(start), _FakeIter(end)

    def get_text(self, start, end, _hidden):
        return self.text[start.position:end.position]

    def begin_user_action(self):
        self.events.append('begin')

    def end_user_action(self):
        self.events.append('end')

    def delete(self, start, end):
        self.text = self.text[:start.position] + self.text[end.position:]
        self.events.append('delete')

    def insert(self, at, text):
        self.text = self.text[:at.position] + text + self.text[at.position:]
        self.events.append('insert')

    def place_cursor(self, at):
        self.caret = at.position

    def select_range(self, end, start):
        self.selection = (start.position, end.position)


class DirectBufferBehaviorTests(unittest.TestCase):
    """Execute the actual editor methods with a no-GTK buffer stub."""

    @staticmethod
    def method(name):
        source = (ROOT / 'artwork_editor.py').read_text()
        cls = next(node for node in ast.parse(source).body
                   if isinstance(node, ast.ClassDef) and node.name == 'ArtworkEditor')
        fn = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                  and node.name == name)
        module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
        scope = {
            'paint_at': paint_at,
            'paint_selection': paint_selection,
            'validate_ink': validate_ink,
            'Adw': types.SimpleNamespace(Toast=types.SimpleNamespace(new=lambda text: text)),
        }
        exec(compile(module, 'artwork_editor.py', 'exec'), scope)
        return scope[name]

    def host(self, buffer, ink='@'):
        notices = []
        editor = types.SimpleNamespace(get_buffer=lambda: buffer,
                                       grab_focus=lambda: None)
        host = types.SimpleNamespace(editor=editor,
                                     _text=lambda: buffer.text,
                                     ink_entry=types.SimpleNamespace(get_text=lambda: ink),
                                     toasts=types.SimpleNamespace(add_toast=notices.append))
        return host, notices

    def test_paint_and_erase_group_changes_without_saving(self):
        buffer = _FakeBuffer('ab\ncd', caret=1)
        host, notices = self.host(buffer)
        self.method('_paint_cell')(host, erase=False)
        self.assertEqual(buffer.text, 'a@\ncd')
        self.assertEqual(buffer.caret, 2)
        self.assertEqual(buffer.events, ['begin', 'delete', 'insert', 'end'])
        buffer.caret = 0
        self.method('_paint_cell')(host, erase=True)
        self.assertEqual(buffer.text, ' @\ncd')
        self.assertEqual(buffer.caret, 1)
        self.assertEqual(notices, [])

    def test_selection_is_paintable_but_invalid_ink_never_overwrites(self):
        buffer = _FakeBuffer('ab\n', caret=1, selection=(0, 2))
        host, notices = self.host(buffer)
        self.method('_paint_cell')(host, erase=False)
        self.assertEqual(buffer.text, '@@\n')
        self.assertFalse(notices)
        self.assertEqual(buffer.events, ['begin', 'delete', 'insert', 'end'])
        buffer.selection = None
        buffer.events.clear()
        host, notices = self.host(buffer, ink='é')
        self.method('_paint_cell')(host, erase=False)
        self.assertEqual(buffer.text, '@@\n')
        self.assertTrue(notices)
        self.assertFalse(buffer.events)

    def test_mirror_fragment_is_single_undo_action_and_selection_retained(self):
        buffer = _FakeBuffer('/>\n ([', selection=(0, 6))
        host, notices = self.host(buffer)
        self.method('_transform_selection')(host, mirror_selection)
        self.assertEqual(buffer.text, ' <\\\n]) ')
        self.assertEqual(buffer.selection, (0, 7))
        self.assertEqual(buffer.events, ['begin', 'delete', 'insert', 'end'])
        self.assertFalse(notices)

    def test_no_selection_transform_does_not_modify_buffer(self):
        buffer = _FakeBuffer('a\nb', caret=0)
        host, notices = self.host(buffer)
        self.method('_transform_selection')(host, flip_selection)
        self.assertEqual(buffer.text, 'a\nb')
        self.assertTrue(notices)
        self.assertFalse(buffer.events)
