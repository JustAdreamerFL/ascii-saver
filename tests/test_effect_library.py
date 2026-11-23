import unittest
from effect_library import select_effects
from playlist_engine import EFFECTS, group

class EffectLibraryTests(unittest.TestCase):
    def test_unfiltered(self):
        self.assertEqual(select_effects(EFFECTS), EFFECTS)
    def test_case_insensitive_search(self):
        self.assertEqual(select_effects(EFFECTS, "MaTrIx"), ["matrix"])
    def test_filters(self):
        self.assertEqual(select_effects(EFFECTS, duration="short"),
                         [name for name in EFFECTS if group(name)["duration"] == "short"])
        self.assertTrue(all(group(name)["intensity"] == "gentle" for name in select_effects(EFFECTS, intensity="gentle")))
    def test_invalid(self):
        with self.assertRaises(ValueError):
            select_effects(EFFECTS, duration="nonsense")

if __name__ == "__main__": unittest.main()
