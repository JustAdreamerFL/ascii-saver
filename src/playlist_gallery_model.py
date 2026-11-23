"""GTK-independent effect-gallery search, category filters and selection counts."""
from __future__ import annotations

from playlist_engine import group


def visible_effects(catalog, *, query="", duration="any", intensity="any"):
    """Return catalog-order matches; filters must never mutate playlist contents."""
    needle = query.strip().casefold()
    result = []
    for effect in catalog:
        category = group(effect)
        if needle and needle not in effect.casefold():
            continue
        if duration != "any" and category["duration"] != duration:
            continue
        if intensity != "any" and category["intensity"] != intensity:
            continue
        result.append(effect)
    return result


def selection_caption(selected, catalog, visible_count):
    """Count saved/draft choices regardless of whether their cards are filtered out."""
    catalog = tuple(catalog)
    selected_count = len(set(selected).intersection(catalog))
    return f"{selected_count} of {len(catalog)} selected · {visible_count} shown"
