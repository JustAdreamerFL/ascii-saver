"""Headless contract and behavior tests for deterministic palette progression."""
from _bootstrap import SRC, read_source  # noqa: F401
import tempfile
from pathlib import Path
import unittest

from helpers import load_config, new_config
from palette_engine import palette_color_for_round, palette_color, palette_for_monitor


ROOT = Path(__file__).resolve().parents[1]


class PaletteRoundTests(unittest.TestCase):
    def setUp(self):
        self.config = new_config()
        self.config.update(palette=['#000000', '#FFFFFF'], cycle_palette=True,
                           palette_steps=2)

    def test_interpolation_between_effects(self):
        self.assertEqual([palette_color_for_round(self.config, None, i)
                          for i in range(5)],
                         ['#000000', '#808080', '#FFFFFF', '#808080', '#000000'])

    def test_steps_one_advances_each_round_and_wraps(self):
        self.config['palette_steps'] = 1
        self.assertEqual([palette_color_for_round(self.config, None, i)
                          for i in range(4)],
                         ['#000000', '#FFFFFF', '#000000', '#FFFFFF'])

    def test_cycle_off_uses_first_color(self):
        self.config['cycle_palette'] = False
        self.assertEqual([palette_color_for_round(self.config, None, i)
                          for i in range(4)], ['#000000'] * 4)

    def test_single_color_never_interpolates(self):
        self.config['palette'] = ['#1A3C5E']
        self.assertEqual(palette_color_for_round(self.config, None, 333), '#1A3C5E')

    def test_same_round_is_idempotent_across_spawn_retries(self):
        self.assertEqual(palette_color_for_round(self.config, 'DP-1', 1),
                         palette_color_for_round(self.config, 'DP-1', 1))
        self.assertNotEqual(palette_color_for_round(self.config, 'DP-1', 1),
                            palette_color_for_round(self.config, 'DP-1', 2))

    def test_shared_palette_matches_across_monitors(self):
        self.assertEqual(palette_color_for_round(self.config, 'DP-1', 1),
                         palette_color_for_round(self.config, 'HDMI-1', 1))

    def test_per_monitor_palettes_follow_same_round_but_have_own_colors(self):
        self.config.update(per_monitor_visuals=True, monitor_visuals={
            'DP-1': {'palette': ['#FF0000', '#00FF00']},
            'HDMI-1': {'palette': ['#0000FF', '#00FFFF']},
        })
        self.assertEqual(palette_color_for_round(self.config, 'DP-1', 1), '#808000')
        self.assertEqual(palette_color_for_round(self.config, 'HDMI-1', 1), '#0080FF')
        self.assertNotEqual(palette_color_for_round(self.config, 'DP-1', 1),
                            palette_color_for_round(self.config, 'HDMI-1', 1))

    def test_unknown_monitor_falls_back_to_shared_palette(self):
        self.config.update(per_monitor_visuals=True, monitor_visuals={
            'DP-1': {'palette': ['#FF0000']},
        })
        self.assertEqual(palette_color_for_round(self.config, 'HDMI-1', 0), '#000000')

    def test_preview_explicitly_ignores_default_named_display_override(self):
        self.config.update(per_monitor_visuals=True, monitor_visuals={
            'default': {'palette': ['#FF0000']},
        })
        self.assertEqual(palette_color_for_round(self.config, None, 0), '#000000')
        self.assertEqual(palette_color_for_round(self.config, 'default', 0), '#FF0000')

    def test_whitespace_in_valid_user_colors_is_safe_to_interpolate(self):
        self.config['palette'] = ['  #ABCDEF  ', ' #123456 ']
        self.assertEqual(palette_color_for_round(self.config, 'DP-1', 0), '#ABCDEF')
        self.assertEqual(palette_color_for_round(self.config, 'DP-1', 2), '#123456')
        self.assertEqual(palette_color_for_round(self.config, 'DP-1', 1), '#5F81A3')

    def test_invalid_override_falls_back_not_crashes(self):
        self.config.update(per_monitor_visuals=True, monitor_visuals={
            'DP-1': {'palette': ['not-a-color']},
        })
        self.assertEqual(palette_color_for_round(self.config, 'DP-1', 1), '#808080')

    def test_empty_palette_fallback(self):
        self.config['palette'] = []
        self.assertEqual(palette_color_for_round(self.config, None, 1), '#F2F2F2')
        self.assertEqual(palette_color((), cycle=True, steps=1, round_index=0), '#F2F2F2')

    def test_non_integer_steps_recover_to_one(self):
        self.config['palette_steps'] = 'bad'
        self.assertEqual(palette_color_for_round(self.config, None, 1), '#FFFFFF')

    def test_real_load_config_accepts_whitespace_padded_palette(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            path.write_text(json.dumps({'palette': ['  #000000  ', ' #FFFFFF '],
                                        'cycle_palette': True, 'palette_steps': 2}))
            loaded = load_config(path)
        self.assertEqual(palette_color_for_round(loaded, 'DP-1', 1), '#808080')


class PaletteWiringTests(unittest.TestCase):
    def test_installer_stages_palette_engine(self):
        installer = (ROOT / 'install.sh').read_text()
        self.assertIn('"$py_src/palette_engine.py" "$staged_app/palette_engine.py"', installer)

    def test_fullscreen_palette_is_clocked_by_shared_round(self):
        text = (SRC / 'app.py').read_text()
        start = text.index('    def _tte_argv(')
        end = text.index('    def _start(', start)
        self.assertIn('palette_round = self.palette_tick if self.windowed else self.app.shared_round', text[start:end])
        self.assertNotIn('self.palette_tick += 1', text[start:end])

    def test_preview_only_advances_palette_after_success(self):
        text = (SRC / 'app.py').read_text()
        start = text.index('    def _on_child_exited(')
        end = text.index('\n\nclass SaverApplication', start)
        callback = text[start:end]
        self.assertLess(callback.index('if tte_exit_ok(status):'),
                        callback.index('self.palette_tick += 1'))
        self.assertLess(callback.index('self.palette_tick += 1'),
                        callback.index('self.app.preview_sequence.advance()'))


if __name__ == '__main__':
    unittest.main()


# Execute the real GTK-free body of SaverWindow._tte_argv with fake VTE.
# This asserts the value actually sent to Vte.Terminal.set_colors, not merely
# the source spelling or a detached helper implementation.
class RendererPaletteIntegrationTests(unittest.TestCase):
    @staticmethod
    def argv_method():
        import ast
        import os
        from types import SimpleNamespace
        source = ast.parse((SRC / 'app.py').read_text())
        saver = next(node for node in source.body
                     if isinstance(node, ast.ClassDef) and node.name == 'SaverWindow')
        method = next(node for node in saver.body
                      if isinstance(node, ast.FunctionDef) and node.name == '_tte_argv')
        module = ast.Module(body=[method], type_ignores=[])
        ast.fix_missing_locations(module)
        scope = dict(Path=Path, os=os,
                     DATA_DIR=Path('/unused-path-for-tests'),
                     palette_color_for_round=palette_color_for_round,
                     parse_color=lambda color, fallback: color)
        exec(compile(module, 'app.py', 'exec'), scope)
        return scope['_tte_argv']

    @staticmethod
    def window(config, *, windowed, monitor_id, round_index=0):
        from types import SimpleNamespace
        foregrounds = []
        class Terminal:
            def set_colors(self, fg, bg, palette):
                foregrounds.append((fg, bg, palette))
        monitor = None if windowed else SimpleNamespace(get_connector=lambda: monitor_id)
        window = SimpleNamespace(
            app=SimpleNamespace(config=config, shared_round=round_index),
            terminal=Terminal(), monitor=monitor,
            monitor_id=monitor_id, windowed=windowed, palette_tick=0,
            _artwork_path=lambda: Path('/tmp/example-artwork.txt'),
        )
        return window, foregrounds

    def test_fullscreen_retries_reuse_actual_vte_foreground(self):
        config = new_config()
        config.update(palette=['#000000', '#FFFFFF'], cycle_palette=True,
                      palette_steps=2)
        window, colors = self.window(config, windowed=False, monitor_id='DP-1', round_index=1)
        method = self.argv_method()
        method(window)
        method(window)
        self.assertEqual([c[0] for c in colors], ['#808080', '#808080'])
        window.app.shared_round = 2
        method(window)
        self.assertEqual(colors[-1][0], '#FFFFFF')

    def test_preview_uses_own_palette_clock(self):
        config = new_config()
        config.update(palette=['#000000', '#FFFFFF'], cycle_palette=True,
                      palette_steps=1, per_monitor_visuals=True,
                      monitor_visuals={'default': {'palette': ['#FF0000']}})
        window, colors = self.window(config, windowed=True, monitor_id='default', round_index=50)
        method = self.argv_method()
        method(window)
        self.assertEqual(colors[-1][0], '#000000')
        window.palette_tick += 1
        method(window)
        self.assertEqual(colors[-1][0], '#FFFFFF')
        self.assertEqual(window.app.shared_round, 50)

    def test_independent_display_palettes_reach_vte(self):
        config = new_config()
        config.update(cycle_palette=True, palette_steps=2,
                      per_monitor_visuals=True, monitor_visuals={
                          'DP-1': {'palette': ['#FF0000', '#00FF00']},
                          'HDMI-1': {'palette': ['#0000FF', '#00FFFF']},
                      })
        method = self.argv_method()
        a, a_colors = self.window(config, windowed=False, monitor_id='DP-1', round_index=1)
        b, b_colors = self.window(config, windowed=False, monitor_id='HDMI-1', round_index=1)
        method(a)
        method(b)
        self.assertEqual(a_colors[-1][0], '#808000')
        self.assertEqual(b_colors[-1][0], '#0080FF')
