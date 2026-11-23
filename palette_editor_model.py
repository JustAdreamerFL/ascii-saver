"""Palette operations shared by GTK controls and headless regression tests.

No implicit changes to the active renderer: edits are committed through Save.
"""
from __future__ import annotations
from helpers import DEFAULT_CONFIG, valid_color

MAX_COLORS = 8
FACTORY_PALETTE = tuple(DEFAULT_CONFIG['palette'])
EXTRA_COLORS = ('#83A7FF', '#D087D8', '#F0BD61', '#5DBEAA', '#D96C6C')

def validate_palette(colors):
    if (not isinstance(colors, (tuple, list)) or not 1 <= len(colors) <= MAX_COLORS
            or not all(valid_color(value) for value in colors)):
        raise ValueError('A palette must contain 1–8 six-digit RGB colors.')
    return tuple('#' + color.lstrip('#').upper() for color in colors)

def add_color(colors):
    current = validate_palette(colors)
    if len(current) >= MAX_COLORS:
        raise ValueError('A palette can contain at most 8 colors.')
    # Use accessible different colors instead of duplicating the last color.
    candidate = (*FACTORY_PALETTE, *EXTRA_COLORS)[len(current)]
    return (*current, candidate)

def remove_color(colors):
    current = validate_palette(colors)
    if len(current) == 1:
        raise ValueError('A palette must contain at least one color.')
    return current[:-1]

def reset_colors():
    return FACTORY_PALETTE
