"""Headless validation of preferences, with no GTK or window system needed."""
import unittest
from preferences_model import validate_form


class FormValidationTests(unittest.TestCase):
    base = dict(playlist_json='[]', playlist_enabled=False, font='Monospace 14',
                background='#000000', excluded_effects=['beams'], monitor_artwork={})

    def check(self, **overrides):
        return validate_form(**(self.base | overrides))

    def test_clean_values_are_saved_without_changes(self):
        values = self.check(monitor_artwork={'DP-1': ' logo.txt ', 'DP-2': ''})
        self.assertEqual(values.monitor_artwork, {'DP-1': 'logo.txt'})
        self.assertEqual(values.excluded_effects, ['beams'])
        self.assertEqual(values.font, 'Monospace 14')

    def test_invalid_paths_produce_feedback(self):
        for name in ('../logo.txt', '/tmp/logo.txt', 'some/file.txt', '.hidden.txt', 'logo.png'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Artwork for'):
                self.check(monitor_artwork={'Portrait display': name})

    def test_palette_and_font_are_validated(self):
        with self.assertRaisesRegex(ValueError, 'Background'):
            self.check(background='transparent')
        with self.assertRaisesRegex(ValueError, 'font'):
            self.check(font='  ')

    def test_invalid_playlist_cannot_be_saved(self):
        with self.assertRaisesRegex(ValueError, 'Playlist format'):
            self.check(playlist_json='{ broken')
        with self.assertRaisesRegex(ValueError, 'Enable at least one playlist'):
            self.check(playlist_enabled=True)

    def test_excluded_names_are_validated(self):
        with self.assertRaisesRegex(ValueError, 'Excluded'):
            self.check(excluded_effects=['-wrong'])
