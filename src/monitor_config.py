"""Pure helpers for display hot-plug and per-display preferences."""
from __future__ import annotations
from collections.abc import Mapping


def extend_monitor_baseline(saved: tuple, current: tuple, added: set[str]) -> tuple:
    """New monitor defaults are saved-state values, not unsaved user edits.

    Preserve every pre-existing form field and its old baseline, including
    pending edits on other displays and any unsaved global settings.
    """
    result = list(saved)
    for index in (7, 8, 9):  # FPS, artwork and palette in _preference_snapshot
        existing = dict(result[index])
        existing.update({key: value for key, value in current[index] if key in added})
        result[index] = tuple(sorted(existing.items()))
    return tuple(result)


def merge_monitor_settings(saved: Mapping, fps: Mapping,
                           artwork: Mapping, palettes: Mapping) -> dict:
    """Keep settings of displays not seen in this Preferences session.

    Only per-display values owned by the UI are updated. Other entries and
    unknown per-monitor visual fields remain intact.
    """
    rates = dict(saved.get("monitor_fps", {}))
    rates.update(fps)
    art = dict(saved.get("monitor_artwork", {}))
    art.update(artwork)
    visuals = {name: dict(value) for name, value in saved.get("monitor_visuals", {}).items()}
    for name, palette in palettes.items():
        visuals.setdefault(name, {})["palette"] = list(palette)
    return {"monitor_fps": rates, "monitor_artwork": art, "monitor_visuals": visuals}
