"""Deterministic per-effect colors shared by fullscreen displays and previews.

A full-screen color is selected by the synchronization round, not by child
spawn attempts. This prevents retries (or a slow secondary monitor) from
skipping ahead in its palette. The persistent preview has its own success-
counted round, so it never consumes fullscreen palette progression.
"""

from __future__ import annotations

from collections.abc import Mapping

from helpers import valid_color


FALLBACK_PALETTE = ("#F2F2F2",)


def _normalized_palette(value: object) -> tuple[str, ...] | None:
    """Use the same RGB format as both GTK and the Rust renderer.

    User-edited config values may be valid yet contain surrounding whitespace.
    Strip that whitespace before slicing hexadecimal pairs for interpolation.
    """
    if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 8:
        return None
    if not all(valid_color(color) for color in value):
        return None
    return tuple(color.strip().upper() for color in value)


def palette_for_monitor(config: Mapping, monitor_id: str | None) -> tuple[str, ...]:
    """Resolve an optional per-display override, or the global palette.

    `None` represents a windowed preview. It intentionally always uses the
    shared palette, even if a display happens to be named ``default``.
    """
    shared = _normalized_palette(config.get("palette")) or FALLBACK_PALETTE
    if monitor_id is None or not config.get("per_monitor_visuals", False):
        return shared
    displays = config.get("monitor_visuals", {})
    if not isinstance(displays, Mapping):
        return shared
    visual = displays.get(monitor_id)
    if not isinstance(visual, Mapping):
        return shared
    return _normalized_palette(visual.get("palette")) or shared


def palette_color(palette: tuple[str, ...], *, cycle: bool,
                  steps: int, round_index: int, ping_pong: bool = False) -> str:
    """Pick one stable foreground color for an entire animation round.

    `steps=1` selects the next palette color every successful effect. Higher
    values linearly interpolate *between* effects, not while drawing a frame.
    Each RGB channel is independently rounded to the nearest integer.
    """
    if not palette:
        palette = FALLBACK_PALETTE
    if not cycle or len(palette) == 1:
        return palette[0]
    if type(steps) is not int or steps < 1:
        steps = 1
    round_index = max(0, round_index)
    index, offset = divmod(round_index, steps)
    if ping_pong and len(palette) > 2:
        # Bounce at the ends rather than jumping directly from last to first.
        path = (*range(len(palette)), *range(len(palette) - 2, 0, -1))
        left = palette[path[index % len(path)]]
        right = palette[path[(index + 1) % len(path)]]
    else:
        left = palette[index % len(palette)]
        right = palette[(index + 1) % len(palette)]
    if offset == 0:
        return left
    rgb = [
        (int(left[pos:pos+2], 16) * (steps - offset)
         + int(right[pos:pos+2], 16) * offset + steps // 2) // steps
        for pos in (1, 3, 5)
    ]
    return "#" + "".join(f"{channel:02X}" for channel in rgb)


def palette_color_for_round(config: Mapping, monitor_id: str | None,
                            round_index: int) -> str:
    """Convenience entry point for both fullscreen and preview renderers."""
    return palette_color(
        palette_for_monitor(config, monitor_id),
        cycle=config.get("cycle_palette", False) is True,
        steps=config.get("palette_steps", 1),
        round_index=round_index,
        ping_pong=config.get("palette_ping_pong", False) is True,
    )


def vte_palette_colors(config: Mapping, monitor_id: str | None = None,
                       round_index: int = 0) -> tuple[str, str]:
    """Return the exact foreground/background used by all VTE playback paths.

    The Rust child is launched with --no-color: its own explicit ANSI/RGB
    foreground and background are suppressed, leaving VTE's configured
    foreground in charge. This keeps the palette authoritative for all effects.
    """
    return (palette_color_for_round(config, monitor_id, round_index),
            config.get("background", "#000000"))


def set_vte_palette(terminal, config: Mapping, gdk, *,
                    monitor_id: str | None = None, round_index: int = 0) -> None:
    """Configure an actual VTE terminal without importing GTK at module load.

    Passing in Gdk keeps palette logic importable by headless tests.
    """
    foreground, background = vte_palette_colors(config, monitor_id, round_index)
    def rgba(value: str, fallback: str):
        color = gdk.RGBA()
        if not color.parse(value):
            color.parse(fallback)
        return color
    terminal.set_colors(rgba(foreground, "#F2F2F2"),
                        rgba(background, "#000000"), [])


def effect_color_arguments(config: Mapping) -> tuple[str, ...]:
    """Apply the terminal palette to all effects only when explicitly enabled.

    With this option disabled, ttfx keeps its own RGB ANSI sequences; the
    chosen palette remains a VTE fallback for effects without explicit color.
    Older configurations default to the previously shipped override behavior.
    """
    return ("--no-color",) if config.get("override_effect_colors", True) is True else ()
