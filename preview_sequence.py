"""A single preview sequence that follows the normal saver timing lifecycle.

The preview owns its own selection cursor so opening it never consumes the
fullscreen screensaver's shared playlist or shuffle state.
"""
from __future__ import annotations
from effect_rotation import EffectShuffleBag
from playlist_engine import EFFECTS


class PreviewSequence:
    def __init__(self, config, scheduler=None, initial_playlist_effect=None, rng=None):
        self._config = config
        self._scheduler = scheduler
        self._bag = EffectShuffleBag(rng=rng)
        self._effect = initial_playlist_effect if config.get("playlist_mode") else None

    def _available(self):
        excluded = set(self._config.get("exclude_effects", ()))
        return [name for name in EFFECTS if name not in excluded]

    def current(self):
        if self._effect is None:
            if self._config.get("playlist_mode") and self._scheduler is not None:
                self._effect = self._scheduler.next()
            else:
                self._effect = self._bag.next(self._available())
        return self._effect

    def advance(self):
        """Call only after a successful completed effect; hold belongs to UI."""
        if self._config.get("playlist_mode") and self._scheduler is not None:
            self._effect = self._scheduler.next()
        else:
            self._effect = self._bag.next(self._available())
        return self._effect
