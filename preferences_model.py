"""GTK-free validation for editable user preferences.

Widgets are deliberately *not* imported here. The same validation can be
run in a headless unit test, a future CLI, or an alternative frontend.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Mapping, Iterable

from helpers import valid_color
from artwork_library import valid_artwork_reference
from playlist_engine import validate as validate_playlists


@dataclass(frozen=True)
class ValidatedForm:
    playlists: list[dict]
    font: str
    background: str
    excluded_effects: list[str]
    monitor_artwork: dict[str, str]


def validate_form(
    *, playlist_json: str, playlist_enabled: bool, font: str,
    background: str, excluded_effects: Iterable[str],
    monitor_artwork: Mapping[str, str],
) -> ValidatedForm:
    """Validate every human-editable free-form value before persistence.

    Invalid monitor artwork names are rejected with an actionable error rather
    than silently removed from the saved configuration.
    """
    try:
        playlists = validate_playlists(json.loads(playlist_json))
    except (ValueError, TypeError) as error:
        raise ValueError(f"Playlist format invalid: {error}") from error
    if playlist_enabled and not any(p["enabled"] for p in playlists):
        raise ValueError("Enable at least one playlist before turning on playlist mode.")
    font = font.strip()
    if not font:
        raise ValueError("Choose a terminal font.")
    if not valid_color(background):
        raise ValueError("Background must be a six-digit #RRGGBB color.")
    excluded = sorted(set(excluded_effects))
    if any(not name or name.startswith("-") for name in excluded):
        raise ValueError("Excluded effect names cannot be empty or start with '-'.")
    artwork = {}
    for monitor, raw in monitor_artwork.items():
        name = raw.strip()
        if not name:
            continue
        if not valid_artwork_reference(name):
            raise ValueError(
                f"Artwork for {monitor}: choose a .txt from the artwork library "
                "or enter a filename in the configuration folder."
            )
        artwork[monitor] = name
    return ValidatedForm(playlists, font, background, excluded, artwork)
