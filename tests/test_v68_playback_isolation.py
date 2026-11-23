"""V68: preview and display playback must not advance each other's history."""
from __future__ import annotations

import ast
import random
import unittest
from pathlib import Path

from effect_rotation import EffectShuffleBag
from effect_selection import select_effect
from playlist_engine import EFFECTS, Scheduler
from preview_sequence import PreviewSequence

ROOT = Path(__file__).resolve().parents[1]


class PlaylistIsolationTests(unittest.TestCase):
    def test_application_wires_separate_preview_and_fullscreen_schedulers(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        application = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                           and node.name == "SaverApplication")
        constructor = next(node for node in application.body if isinstance(node, ast.FunctionDef)
                           and node.name == "__init__")
        body = ast.get_source_segment(source, constructor)
        self.assertIn('self.playlist_scheduler = Scheduler(playlists, excluded)', body)
        self.assertIn('self.preview_playlist_scheduler = Scheduler(playlists, excluded)', body)
        self.assertIn('PreviewSequence(self.config, self.preview_playlist_scheduler)', body)
        self.assertNotIn('PreviewSequence(self.config, self.playlist_scheduler', body)

    def test_preview_sequence_does_not_advance_fullscreen_cursor(self):
        playlists = [{"name": "Sequence", "enabled": True, "order": "sequential",
                      "effects": ["rain", "waves", "print"]}]
        saver_scheduler = Scheduler(playlists)
        preview_scheduler = Scheduler(playlists)
        saver_first = saver_scheduler.next()
        preview = PreviewSequence({"playlist_mode": True}, preview_scheduler)
        self.assertEqual(saver_first, "rain")
        self.assertEqual(preview.current(), "rain")
        self.assertEqual(preview.advance(), "waves")
        self.assertEqual(preview.advance(), "print")
        self.assertEqual(saver_scheduler.next(), "waves")

    def test_fullscreen_bag_and_preview_bag_are_independent(self):
        allowed = list(EFFECTS[:4])
        config = {"exclude_effects": [effect for effect in EFFECTS if effect not in allowed]}
        monitor_bag = EffectShuffleBag(random.Random(7))
        other_bag = EffectShuffleBag(random.Random(7))
        preview_bag = EffectShuffleBag(random.Random(7))
        a = [select_effect(config, rotation=monitor_bag) for _ in allowed]
        b = [select_effect(config, rotation=other_bag) for _ in allowed]
        c = [select_effect(config, rotation=preview_bag) for _ in allowed]
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(set(a), set(allowed))
        self.assertNotEqual(a[-1], select_effect(config, rotation=monitor_bag))

    def test_explicit_playlist_and_shared_effect_take_priority_over_shuffle(self):
        config = {"exclude_effects": ["matrix"]}
        bag = EffectShuffleBag(random.Random(4))
        self.assertEqual(select_effect(config, playlist_effect="waves", shared_effect="rain",
                                       rotation=bag), "waves")
        self.assertEqual(select_effect(config, playlist_effect="matrix", shared_effect="rain",
                                       rotation=bag), "rain")
        self.assertIsNone(bag.available)  # no bag entry consumed for explicit effects
        self.assertNotEqual(select_effect(config, rotation=bag), "matrix")

    def test_bags_reset_when_allowed_effects_change(self):
        bag = EffectShuffleBag(random.Random(3))
        one = {"exclude_effects": [name for name in EFFECTS if name not in ("rain", "waves")]}
        self.assertIn(select_effect(one, rotation=bag), ("rain", "waves"))
        new = {"exclude_effects": [name for name in EFFECTS if name != "print"]}
        self.assertEqual(select_effect(new, rotation=bag), "print")

    def test_fullscreen_window_owns_a_private_shuffle_bag(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('self._effect_bag = EffectShuffleBag()', source)
        self.assertIn('rotation=self._effect_bag', source)


class ShuffledPlaylistTests(unittest.TestCase):
    def test_playlist_shuffle_avoids_immediate_repeat_between_cycles(self):
        playlists = [{"name": "Shuffle", "order": "shuffle", "enabled": True,
                      "effects": ["rain", "waves", "print"]}]
        scheduler = Scheduler(playlists, seed=21)
        cycles = [[scheduler.next() for _ in range(3)] for _ in range(25)]
        for cycle in cycles:
            self.assertEqual(set(cycle), {"rain", "waves", "print"})
        for before, after in zip(cycles, cycles[1:]):
            self.assertNotEqual(before[-1], after[0])

    def test_single_available_effect_can_repeat(self):
        scheduler = Scheduler([{"name": "Single", "order": "shuffle", "enabled": True,
                                "effects": ["rain"]}], seed=1)
        self.assertEqual([scheduler.next() for _ in range(4)], ["rain"] * 4)


if __name__ == "__main__":
    unittest.main()
