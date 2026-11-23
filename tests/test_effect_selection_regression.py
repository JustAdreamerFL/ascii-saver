import unittest
from effect_selection import effect_args, select_effect


class EffectArgumentsTests(unittest.TestCase):
    def test_exclusions_do_not_strip_terminal_flags(self):
        args = ["ttfx", "--frame-rate", "60", "--random-effect", "--exclude-effects", "matrix", "rain", "--no-eol", "--no-restore-cursor"]
        self.assertEqual(effect_args(args, "beams"), ["ttfx", "--frame-rate", "60", "--no-eol", "--no-restore-cursor", "beams"])

    def test_explicit_effect_has_one_subcommand(self):
        self.assertEqual(effect_args(["ttfx", "--no-eol", "rain"], "beams"), ["ttfx", "--no-eol", "beams"])

    def test_new_builder_maintains_options(self):
        args = ["ttfx", "-i", "/tmp/logo.txt", "--no-eol", "--frame-rate", "100"]
        self.assertEqual(effect_args(args, "matrix"), args + ["matrix"])

    def test_unknown_effect_rejected(self):
        with self.assertRaises(ValueError):
            effect_args(["ttfx"], "nope")

    def test_excluded_effect_never_selected(self):
        self.assertEqual(select_effect({"exclude_effects":["matrix"]}, playlist_effect="matrix", shared_effect="rain"), "rain")

if __name__ == "__main__":
    unittest.main()
