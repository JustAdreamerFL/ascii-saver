"""Palette direction, persistence and cross-display deterministic behavior."""
from _bootstrap import SRC, read_source  # noqa: F401
import json
import tempfile
import unittest
from pathlib import Path
from helpers import load_config, new_config
from palette_engine import palette_color_for_round

class PaletteBounceTests(unittest.TestCase):
    def setUp(self):
        self.config = new_config()
        self.config.update(palette=["#FF0000", "#00FF00", "#0000FF"], cycle_palette=True, palette_ping_pong=True, palette_steps=1)

    def test_three_color_bounce(self):
        self.assertEqual([palette_color_for_round(self.config, None, i) for i in range(9)], ["#FF0000", "#00FF00", "#0000FF", "#00FF00", "#FF0000", "#00FF00", "#0000FF", "#00FF00", "#FF0000"])

    def test_interpolation_on_reverse(self):
        self.config["palette_steps"] = 2
        self.assertEqual(palette_color_for_round(self.config, None, 5), "#008080")
        self.assertEqual(palette_color_for_round(self.config, None, 7), "#808000")

    def test_old_loop_is_unchanged(self):
        self.config["palette_ping_pong"] = False
        self.assertEqual(palette_color_for_round(self.config, None, 3), "#FF0000")

    def test_two_color_bounce_is_same_as_loop(self):
        self.config["palette"] = ["#FF0000", "#00FF00"]
        self.assertEqual([palette_color_for_round(self.config, None, i) for i in range(4)], ["#FF0000", "#00FF00", "#FF0000", "#00FF00"])

    def test_preview_and_monitor_same_round(self):
        self.assertEqual(palette_color_for_round(self.config, None, 3), palette_color_for_round(self.config, "DP-1", 3))

    def test_per_monitor_colors_still_independent(self):
        self.config.update(per_monitor_visuals=True, monitor_visuals={"DP-1": {"palette": ["#111111", "#222222", "#333333"]}})
        self.assertEqual(palette_color_for_round(self.config, "DP-1", 2), "#333333")
        self.assertEqual(palette_color_for_round(self.config, "HDMI-1", 2), "#0000FF")

    def test_config_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/"config.json"
            file.write_text(json.dumps({"palette_ping_pong": True}))
            self.assertTrue(load_config(file)["palette_ping_pong"])
            file.write_text(json.dumps({"palette_ping_pong": "yes"}))
            self.assertFalse(load_config(file)["palette_ping_pong"])

    def test_default_legacy_behavior(self):
        self.assertFalse(new_config()["palette_ping_pong"])

if __name__ == "__main__": unittest.main()
