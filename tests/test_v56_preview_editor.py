"""V56 preview lifecycle, artwork editing and install regression checks."""
from _bootstrap import SRC, read_source  # noqa: F401
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from preview_sequence import PreviewSequence
from artwork_editor_io import read_artwork, save_artwork
from playlist_engine import EFFECTS

ROOT = Path(__file__).resolve().parents[1]


class PreviewSequenceTests(unittest.TestCase):
    def test_random_preview_rotates_all_effects_before_repeating(self):
        allowed = list(EFFECTS[:4])
        config = {"playlist_mode": False,
                  "exclude_effects": [name for name in EFFECTS if name not in allowed]}
        seq = PreviewSequence(config, rng=random.Random(8))
        first = [seq.current()] + [seq.advance() for _ in range(3)]
        self.assertEqual(set(first), set(allowed))
        self.assertNotEqual(first[-1], seq.advance())
        self.assertEqual(seq.current(), seq.current())

    def test_ordered_playlist_preview_advances_its_scheduler(self):
        sched = Mock()
        sched.next.side_effect = ["matrix", "beams", "print"]
        seq = PreviewSequence({"playlist_mode": True}, sched, "waves")
        self.assertEqual(seq.current(), "waves")
        self.assertEqual(seq.advance(), "matrix")
        self.assertEqual(seq.advance(), "beams")
        self.assertEqual(sched.next.call_count, 2)

    def test_only_one_effect_enabled_repeats_intentionally(self):
        chosen = EFFECTS[0]
        config = {"exclude_effects": [name for name in EFFECTS if name != chosen]}
        seq = PreviewSequence(config)
        self.assertEqual(seq.current(), chosen)
        self.assertEqual(seq.advance(), chosen)


class ArtworkEditorIOTests(unittest.TestCase):
    def test_utf8_ascii_art_is_written_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            art = Path(directory, 'art.txt')
            art.write_text('before\n', encoding='utf-8')
            save_artwork(art, '░▓▒\nsecond line\n')
            self.assertEqual(read_artwork(art), '░▓▒\nsecond line\n')
            self.assertEqual([p.name for p in Path(directory).iterdir()], ['art.txt'])

    def test_editor_does_not_create_new_art_by_accident(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                save_artwork(Path(directory, 'missing.txt'), 'x')


class IntegrationContracts(unittest.TestCase):
    def test_preview_use_standalone_sequence_and_hold(self):
        src = (SRC / 'app.py').read_text()
        self.assertIn('self.app.preview_sequence.current()', src)
        self.assertIn('self.app.preview_sequence.advance()', src)
        self.assertIn('hold_ms + TTE_SUCCESS_RESTART_MS', src)

    def test_auto_fit_is_available_in_shared_and_independent_modes(self):
        src = (SRC / 'app.py').read_text()
        self.assertIn('choose_artwork_font_sizes(', src)
        self.assertIn('independent = bool(self.app.config.get("per_monitor", False))', src)
        self.assertIn('self.terminal.set_font(desc)', src)
        display_src = (SRC / 'preferences_displays.py').read_text()
        self.assertNotIn('self.auto_fit_artwork.set_active(False)', display_src)
        pages_src = (SRC / 'preferences_pages.py').read_text()
        self.assertIn('self.section_groups["displays"].add(self.auto_fit_artwork)', pages_src)
        self.assertNotIn('monitor_options.add(self.auto_fit_artwork)', pages_src)

    def test_dashboard_refresh_is_immediate_after_save(self):
        src = (SRC / 'preferences_state.py').read_text()
        self.assertIn('dashboard._refresh_status()', src)
        self.assertIn('self._set_notice("Saved.")', src)

    def test_editor_installed_not_only_in_source(self):
        src = (ROOT / 'install.sh').read_text()
        self.assertIn('artwork_editor artwork_editor_io', src)
        self.assertIn('preview_sequence.py', src)

if __name__ == '__main__':
    unittest.main()
