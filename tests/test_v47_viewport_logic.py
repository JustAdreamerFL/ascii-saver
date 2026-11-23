"""Exercise viewport selection without requiring a GTK display or gi install."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def load_with_stubbed_gi():
    gi = types.ModuleType('gi')
    gi.require_version = lambda *args: None
    repository = types.ModuleType('gi.repository')
    repository.Gdk = types.SimpleNamespace()
    repository.GLib = types.SimpleNamespace(SOURCE_REMOVE=False)
    repository.Gtk = types.SimpleNamespace(Picture=object, ScrolledWindow=object)
    gi.repository = repository
    spec = importlib.util.spec_from_file_location('_preview_test_viewport', ROOT / 'animated_preview.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'gi': gi, 'gi.repository': repository}):
        spec.loader.exec_module(module)
    return module


class FakeScroller:
    def get_mapped(self): return True
    def get_height(self): return 200
    def get_width(self): return 500


class FakeCard:
    def __init__(self, y, width=240, height=140):
        self.y, self.width, self.height = y, width, height
    def get_mapped(self): return True
    def get_visible(self): return True
    def translate_coordinates(self, *_): return True, 0.0, self.y
    def get_height(self): return self.height
    def get_width(self): return self.width


class FakePreview:
    def __init__(self): self.playing = None
    def set_playing(self, playing): self.playing = playing


class ViewportTests(unittest.TestCase):
    def test_only_visible_card_plays_and_scroll_switches_active_card(self):
        module = load_with_stubbed_gi()
        first, second = FakePreview(), FakePreview()
        one, two = FakeCard(50), FakeCard(550)
        entries = [(one, first), (two, second)]
        self.assertFalse(module.update_visible_previews(FakeScroller(), entries))
        self.assertTrue(first.playing)
        self.assertFalse(second.playing)
        one.y, two.y = -650, 40
        module.update_visible_previews(FakeScroller(), entries)
        self.assertFalse(first.playing)
        self.assertTrue(second.playing)


if __name__ == '__main__': unittest.main()
