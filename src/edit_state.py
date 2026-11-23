"""Small GTK-independent snapshots for explicit Save / Discard workflows.

A window may edit only a subset of shared preferences. Updating its baseline
must not accidentally mark unrelated pending preferences as saved.
"""
from __future__ import annotations
from copy import deepcopy


class EditBaseline:
    def __init__(self, value):
        self._saved = deepcopy(value)

    def changed(self, value) -> bool:
        return value != self._saved

    def commit(self, value) -> None:
        self._saved = deepcopy(value)

    def restore(self):
        return deepcopy(self._saved)


def merge_saved_fields(saved: tuple, current: tuple, indices: tuple[int, ...]) -> tuple:
    """Mark only the explicitly persisted fields as saved, not the full form."""
    if len(saved) != len(current):
        raise ValueError("snapshot lengths differ")
    positions = set(indices)
    if any(index < 0 or index >= len(saved) for index in positions):
        raise ValueError("snapshot field index out of bounds")
    return tuple(current[i] if i in positions else old for i, old in enumerate(saved))
