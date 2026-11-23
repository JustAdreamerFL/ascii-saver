"""GTK-free tests for the first creative Artwork Studio milestone increment."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest

from artwork_templates import TEMPLATES, get_template
from artwork_editor_io import read_artwork, save_artwork

ROOT = Path(__file__).resolve().parents[1]


def method(name):
    source = (SRC / 'artwork_editor.py').read_text()
    klass = next(item for item in ast.parse(source).body
                 if isinstance(item, ast.ClassDef) and item.name == 'ArtworkEditor')
    fn = next(item for item in klass.body if isinstance(item, ast.FunctionDef)
              and item.name == name)
    mod = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    scope = {}
    exec(compile(mod, 'artwork_editor.py', 'exec'), scope)
    return scope[name]


class TemplateMilestoneTests(unittest.TestCase):
    def test_styles_are_varied_original_offline_editable_text_not_just_sizes(self):
        self.assertGreaterEqual(len(TEMPLATES), 8)
        self.assertEqual(len({item.key for item in TEMPLATES}), len(TEMPLATES))
        self.assertEqual(len({item.artwork for item in TEMPLATES}), len(TEMPLATES))
        self.assertGreaterEqual(len({item.style.split(' · ')[0] for item in TEMPLATES}), 8)
        for template in TEMPLATES:
            with self.subTest(style=template.key):
                self.assertTrue(template.title and template.description and template.style)
                self.assertGreaterEqual(len(template.artwork.splitlines()), 5)
                self.assertTrue(template.artwork.endswith('\n'))
                self.assertLess(max(map(len, template.artwork.splitlines())), 75)
                self.assertTrue(template.artwork.isascii())
                self.assertNotIn('\x00', template.artwork)
                self.assertEqual(get_template(template.key), template)

    def test_unknown_template_id_does_not_fallback_or_load_external_files(self):
        with self.assertRaises(KeyError):
            get_template('../../home/user/private.txt')
        with self.assertRaises(KeyError):
            get_template('')

    def test_chooser_uses_search_preview_and_real_responsive_orientation(self):
        source = (SRC / 'artwork_templates_view.py').read_text()
        for required in ('Gtk.SearchEntry', 'self.listbox.set_filter_func',
                         "self.preview = Gtk.TextView(editable=False",
                         'self.preview.get_buffer().set_text(template.artwork)',
                         "Adw.BreakpointCondition.parse('max-width: 690sp')",
                         "narrow.add_setter(columns, 'orientation', Gtk.Orientation.VERTICAL)",
                         "choose.connect('clicked', self._use_selected)"):
            self.assertIn(required, source)
        self.assertLess(source.index('self._row_templates[row] = template'),
                        source.index('self.listbox.append(row)'))
        self.assertNotIn('save_artwork(', source)
        self.assertNotIn('subprocess', source)

    def test_template_application_only_changes_buffer_not_user_file(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'art.txt'
            path.write_text('Original artwork\n', encoding='utf-8')
            buffer = types.SimpleNamespace(text='Original artwork\n',
                                           set_text=lambda value: setattr(buffer, 'text', value))
            editor = types.SimpleNamespace(get_buffer=lambda: buffer, grab_focus=lambda: None)
            picker = types.SimpleNamespace(closed=0)
            picker.close = lambda: setattr(picker, 'closed', picker.closed + 1)
            host = types.SimpleNamespace(editor=editor)
            method('_replace_with_template')(host, TEMPLATES[0], picker)
            self.assertEqual(buffer.text, TEMPLATES[0].artwork)
            self.assertEqual(picker.closed, 1)
            self.assertEqual(read_artwork(path), 'Original artwork\n')
            save_artwork(path, buffer.text)
            self.assertEqual(read_artwork(path), TEMPLATES[0].artwork)

    def test_dirty_buffer_requires_confirmation_without_replacement(self):
        accepted = []
        host = types.SimpleNamespace(original_text='Saved value',
                                     _text=lambda: 'Unsaved handwritten edits',
                                     _confirm_template_replace=lambda t, p: accepted.append(('confirm', t, p)),
                                     _replace_with_template=lambda t, p: accepted.append(('replace', t, p)))
        picker = object()
        method('_use_template')(host, TEMPLATES[2], picker)
        self.assertEqual(accepted, [('confirm', TEMPLATES[2], picker)])
        accepted.clear()
        host._text = lambda: 'Saved value'
        method('_use_template')(host, TEMPLATES[2], picker)
        self.assertEqual(accepted, [('replace', TEMPLATES[2], picker)])

    def test_existing_editor_save_and_close_safety_remain(self):
        src = (SRC / 'artwork_editor.py').read_text()
        self.assertIn('self.connect("close-request", self._close_requested)', src)
        self.assertIn('if self._text() != self.original_text and not self._close_confirmed:', src)
        self.assertIn('self._saved_count += 1', src)
        self.assertIn('def _open_templates', src)
        self.assertIn('if self._templates_window is not None:', src)
        self.assertIn('Replace unsaved edits?', src)

    def test_installer_and_release_roadmap_are_synchronized(self):
        installer = (ROOT / 'install.sh').read_text()
        self.assertIn('artwork_templates artwork_templates_view', installer)
        self.assertGreaterEqual(tuple(map(int, (ROOT / 'VERSION').read_text().strip().split('.'))), (0, 86, 0))
        self.assertIn('## 0.86.0 (experimental) - 2026-11-08',
                      (ROOT / 'CHANGELOG.md').read_text())
        self.assertIn('M1: Artwork Studio', (ROOT / 'ROADMAP.md').read_text())
        self.assertIn('## Artwork Studio milestone', (ROOT / 'TASKS.md').read_text())
        self.assertIn('## Newly approved future milestone', (ROOT / 'MASTER-BACKLOG.md').read_text())
        self.assertTrue((ROOT / 'docs/archive/UX-ROADMAP-V54.md').is_file())
        self.assertIn('GTK', (ROOT / 'docs/releases/RELEASE-V86.md').read_text())


if __name__ == '__main__':
    unittest.main()
