"""Randomized without-replacement effect rotation for synchronized displays."""
import random

class EffectShuffleBag:
    def __init__(self, rng=None):
        self.rng = rng or random.SystemRandom()
        self.remaining = []
        self.previous = None
        self.available = None

    def next(self, choices):
        available = tuple(dict.fromkeys(choices))
        if not available:
            raise ValueError("No enabled effects")
        if available != self.available:
            self.available = available
            self.remaining.clear()
        if not self.remaining:
            self.remaining = list(available)
            self.rng.shuffle(self.remaining)
            if len(self.remaining) > 1 and self.remaining[-1] == self.previous:
                # Pop occurs from the end; avoid repeating at bag boundaries.
                self.remaining[-1], self.remaining[0] = self.remaining[0], self.remaining[-1]
        result = self.remaining.pop()
        self.previous = result
        return result
