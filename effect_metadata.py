"""Human-readable, qualitative effect metadata for both effect galleries.

Duration is a suggested grouping, never a measured rendering duration.
"""
from __future__ import annotations
from playlist_engine import group


def effect_caption(name: str) -> str:
    classification = group(name)
    return f"{classification['duration'].capitalize()} · {classification['intensity'].capitalize()}"
