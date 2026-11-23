"""V71: palette wins over effect-generated RGB on every live VTE surface.

These run without GTK. The executable's --no-color formatting behavior is
checked against Rust source, since a Rust toolchain is not installed here.
"""
from _bootstrap import SRC, read_source  # noqa: F401
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from helpers import new_config
from palette_engine import set_vte_palette, vte_palette_colors

ROOT = Path(__file__).resolve().parents[1]


class FakeGdk:
    class RGBA:
        def __init__(self):
            self.value = None
        def parse(self, value):
            if isinstance(value, str) and len(value) == 7 and value[0] == '#':
                try:
                    int(value[1:], 16)
                except ValueError:
                    return False
                self.value = value.upper()
                return True
            return False


class FakeTerminal:
    def __init__(self):
        self.calls = []
    def set_colors(self, foreground, background, palette):
        self.calls.append((foreground.value, background.value, palette))


class VtePaletteTests(unittest.TestCase):
    def test_palette_applied_to_terminal_and_background_preserved(self):
        cfg = new_config()
        cfg.update(palette=['#1369AE'], background='#010203', cycle_palette=False)
        terminal = FakeTerminal()
        set_vte_palette(terminal, cfg, FakeGdk)
        self.assertEqual(terminal.calls, [('#1369AE', '#010203', [])])

    def test_independent_displays_apply_different_colors_same_round(self):
        cfg = new_config()
        cfg.update(cycle_palette=True, palette_steps=2, per_monitor_visuals=True,
                   monitor_visuals={'DP-1': {'palette': ['#000000', '#FF0000']},
                                    'HDMI-1': {'palette': ['#000000', '#0000FF']}})
        a, b = FakeTerminal(), FakeTerminal()
        set_vte_palette(a, cfg, FakeGdk, monitor_id='DP-1', round_index=1)
        set_vte_palette(b, cfg, FakeGdk, monitor_id='HDMI-1', round_index=1)
        self.assertEqual(a.calls[0][0], '#800000')
        self.assertEqual(b.calls[0][0], '#000080')
        self.assertEqual(vte_palette_colors(cfg, None, 0)[0], cfg['palette'][0])

    def test_invalid_background_uses_terminal_fallback(self):
        cfg = new_config()
        cfg['background'] = 'broken'
        terminal = FakeTerminal()
        set_vte_palette(terminal, cfg, FakeGdk)
        self.assertEqual(terminal.calls[0][1], '#000000')

    def test_unsaved_palette_is_used_by_real_preferences_method(self):
        tree = ast.parse((SRC / 'preferences_state.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == 'PreferenceStateMixin')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                      and n.name == '_preview_palette_config')
        ast.fix_missing_locations(method)
        scope = {'load_config': lambda _: new_config(),
                 'ctl': SimpleNamespace(config_file=Path('/does/not/matter'))}
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'preferences_state.py', 'exec'), scope)
        obj = SimpleNamespace(
            palette_entries=['red', 'blue'], background='background',
            cycle_palette=SimpleNamespace(get_active=lambda: True),
            palette_steps=SimpleNamespace(get_value_as_int=lambda: 2),
            _rgba_hex=lambda button: {'red':'#FF0000', 'blue':'#0000FF',
                                      'background':'#101010'}[button],
        )
        cfg = scope['_preview_palette_config'](obj)
        self.assertEqual(cfg['palette'], ['#FF0000', '#0000FF'])
        self.assertEqual(cfg['background'], '#101010')
        self.assertTrue(cfg['cycle_palette'])
        self.assertEqual(cfg['palette_steps'], 2)


class PaletteRendererContractTests(unittest.TestCase):
    def test_all_live_renderers_launch_ttfx_without_effect_rgb(self):
        for name in ('app.py', 'preferences_gallery.py', 'effect_preview_window.py'):
            with self.subTest(name=name):
                code = read_source(name)
                tree = ast.parse(code)
                argv_lists = [node for node in ast.walk(tree)
                              if isinstance(node, ast.List)
                              and any(isinstance(v, ast.Constant) and v.value in
                                      ('--frame-rate',) for v in node.elts)]
                self.assertTrue(argv_lists, 'ttfx launch args not found')
                for argv in argv_lists:
                    self.assertFalse(any(isinstance(v, ast.Constant) and v.value == '--no-color'
                                         for v in argv.elts), f'{name} hard-coded --no-color')
                self.assertIn('override_effect_colors' if name == 'app.py' else 'effect_color_arguments', code)

    def test_library_previews_use_current_swatches(self):
        code = (SRC / 'preferences_gallery.py').read_text()
        self.assertGreaterEqual(code.count('self._preview_palette_config()'), 2)
        self.assertIn('set_vte_palette(terminal, self._preview_palette_config(), Gdk)', code)
        self.assertIn('palette_config=self._preview_palette_config()', code)
        code = (SRC / 'effect_preview_window.py').read_text()
        self.assertIn('set_vte_palette(terminal, config, Gdk)', code)

    def test_rust_no_color_path_prevents_explicit_rgb_and_xterm_colors(self):
        rust = (ROOT / 'ttfx-rust/src/fx/visual.rs').read_text()
        start = rust.index('fn format_visual(')
        end = rust.index('/// The attributes and colors:', start)
        body = rust[start:end]
        self.assertIn('if !no_color {', body)
        self.assertIn('sgr.color(fg, b"38", xterm);', body)
        self.assertIn('sgr.color(bg, b"48", xterm);', body)
        cli = (ROOT / 'ttfx-rust/src/cli.rs').read_text()
        self.assertIn('#[arg(long = "no-color", default_value_t = false)]', cli)
        self.assertIn('no_color: self.no_color', cli)
        engine = (ROOT / 'ttfx-rust/src/fx/mod.rs').read_text()
        self.assertIn('VisualPool::new(config.no_color, config.xterm_colors)', engine)


if __name__ == '__main__':
    unittest.main()
