"""Execute the actual renderer font-fit method without importing GTK/VTE."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
import sys

from artwork_fit import artwork_cells, choose_artwork_font_sizes

ROOT = Path(__file__).resolve().parents[1]


def fit_method():
    source = ast.parse((SRC / 'app.py').read_text(encoding='utf-8'))
    klass = next(x for x in source.body if isinstance(x, ast.ClassDef)
                 and x.name == 'SaverWindow')
    method = next(x for x in klass.body if isinstance(x, ast.FunctionDef)
                  and x.name == '_auto_fit_monitor_artwork')
    mod = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(mod)

    class FontDesc:
        def __init__(self, points):
            self.size = round(points * 1024)

        def get_size(self):
            return self.size

        def set_size(self, size):
            self.size = size

    namespace = {
        'Pango': SimpleNamespace(
            SCALE=1024, FontDescription=SimpleNamespace(
                from_string=lambda text: FontDesc(float(text.split()[-1])))),
        'artwork_cells': artwork_cells,
        'choose_artwork_font_sizes': choose_artwork_font_sizes,
        'sys': sys,
    }
    exec(compile(mod, 'app.py', 'exec'), namespace)
    return namespace['_auto_fit_monitor_artwork']


FIT = fit_method()


class Monitor:
    def __init__(self, connector, width, height):
        self.connector = connector
        self.width = width
        self.height = height

    def get_connector(self):
        return self.connector

    def get_model(self):
        return self.connector

    def get_geometry(self):
        return SimpleNamespace(width=self.width, height=self.height)


class Terminal:
    def __init__(self):
        self.point_sizes = []

    def set_font(self, font):
        self.point_sizes.append(font.get_size() / 1024)

    def get_char_width(self):
        return 10

    def get_char_height(self):
        return 20


class RendererFontFitRuntime(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.logo = Path(self.tmp.name) / 'logo.txt'
        self.logo.write_text('X' * 120 + '\n' + 'Y' * 25 + '\n', encoding='utf-8')
        self.wide = Monitor('DP-1', 1800, 800)
        self.narrow = Monitor('DP-2', 800, 1200)
        self.config = {'font': 'Monospace 18', 'auto_fit_artwork': True,
                       'per_monitor': True}
        self.app = SimpleNamespace(config=self.config,
                                   _monitors=SimpleNamespace(
                                       get_n_items=lambda: 2,
                                       get_item=lambda i: [self.wide, self.narrow][i]))

    def create_window(self, monitor):
        return SimpleNamespace(app=self.app, terminal=Terminal(), monitor=monitor,
                               monitor_id=monitor.connector,
                               current_artwork_path=self.logo)

    def run_fit(self, window):
        with redirect_stderr(StringIO()):
            FIT(window)
        return window.terminal.point_sizes[-1]

    def test_independent_fit_uses_own_monitor(self):
        self.assertEqual(self.run_fit(self.create_window(self.wide)), 18)
        self.assertLess(self.run_fit(self.create_window(self.narrow)), 18)

    def test_shared_fit_uses_same_smallest_display_on_both(self):
        self.config['per_monitor'] = False
        wide = self.run_fit(self.create_window(self.wide))
        narrow = self.run_fit(self.create_window(self.narrow))
        self.assertLess(wide, 18)
        self.assertEqual(wide, narrow)

    def test_disabling_auto_fit_restores_font_after_previous_shrink(self):
        window = self.create_window(self.narrow)
        self.assertLess(self.run_fit(window), 18)
        self.config['auto_fit_artwork'] = False
        self.assertEqual(self.run_fit(window), 18)
        self.assertEqual(window.terminal.point_sizes[-1], 18)

    def test_changing_to_shared_mode_recalculates_from_baseline(self):
        window = self.create_window(self.wide)
        self.assertEqual(self.run_fit(window), 18)
        self.config['per_monitor'] = False
        self.assertLess(self.run_fit(window), 18)
        self.config['per_monitor'] = True
        self.assertEqual(self.run_fit(window), 18)


if __name__ == '__main__':
    unittest.main()
