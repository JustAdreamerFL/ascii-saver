"""Deterministic contract for Surprise Me selection, independently testable."""
from __future__ import annotations
import secrets

def choose_surprise(identifiers, previous=None, chooser=None):
    candidates = tuple(dict.fromkeys(identifiers))
    if not candidates:
        return None
    alternatives = tuple(item for item in candidates if item != previous)
    pool = alternatives or candidates
    return (chooser or secrets.choice)(pool)


def prioritize_selection(items, identifier):
    """Keep the chosen artwork in the *loaded* gallery page after sorting.

    Paged GTK list views cannot select an artwork on an unseen page. Move only
    the chosen item to the front, leaving the remaining shuffled order intact.
    """
    ordered = list(items)
    if identifier is None:
        return ordered
    index = next((i for i, item in enumerate(ordered)
                  if getattr(item, 'number', None) == identifier), None)
    if index is None:
        return ordered
    return [ordered.pop(index), *ordered]
