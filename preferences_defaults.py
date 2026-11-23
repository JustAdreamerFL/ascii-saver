"""Explicit factory-default affordances for numeric preferences.

Factory defaults never come from the user's saved config; changing a saved
preference back to its factory default is itself an unsaved edit until saved.
"""
from __future__ import annotations

from helpers import DEFAULT_CONFIG


NUMERIC_DEFAULTS = {
    "delay": ("idle_delay", 120),
    "frame_rate": ("frame_rate", 60),
    "effect_hold": ("effect_hold_seconds", 3.0),
    "speed": ("speed", 1.0),
    "duration_factor": ("duration_factor", 1.0),
    "time_scale": ("time_scale", 1.0),
    "simulation_hold": ("simulation_hold", 1),
    "palette_steps": ("palette_steps", 1),
}


def default_for(control: str) -> float:
    """Read from the application's factory model, never from config.json."""
    key, fallback = NUMERIC_DEFAULTS[control]
    return float(DEFAULT_CONFIG.get(key, fallback))


def is_factory_default(value: float, default: float) -> bool:
    return abs(float(value) - float(default)) < 0.000001


def install_numeric_reset(row, control, default, Gtk):
    """Add a reset action on the right, visible only when not at the default."""
    reset = Gtk.Button.new_from_icon_name("edit-undo-symbolic")
    reset.add_css_class("flat")
    reset.set_tooltip_text(f"Restore default: {default:g}")

    # Reserve space even at factory value. Hiding the widget would resize the
    # whole Adw.ActionRow, causing its slider and label to jump horizontally.
    def update(*_args):
        modified = not is_factory_default(control.get_value(), default)
        reset.set_opacity(1.0 if modified else 0.0)
        reset.set_sensitive(modified)
        reset.set_focusable(modified)

    reset.connect("clicked", lambda *_args: control.set_value(default))
    control.connect("value-changed", update)
    row.add_suffix(reset)
    update()
    return reset
