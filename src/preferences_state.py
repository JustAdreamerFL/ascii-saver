"""Configuration read/write, validation, and change tracking."""
from __future__ import annotations
import os
import sys
import json
import signal
import threading
import subprocess
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, Pango
import ctl
from helpers import load_config, valid_color
from playlist_engine import validate, DEFAULT_PLAYLISTS
from effect_library import select_effects
from animated_preview import update_visible_previews
from effect_preview_window import EffectPreviewWindow
from effect_profiles import read_records, profile
from performance_ui import PerformanceWindow
from effect_catalog import EFFECTS
from palette_engine import palette_color_for_round
from preferences_model import validate_form
from edit_state import EditBaseline
from monitor_config import merge_monitor_settings

class PreferenceStateMixin:
    def _connect_dirty_signals(self):
        controls = [self.enabled, self.respect_inhibitors, self.ignore_fullscreen,
                    self.per_monitor, self.per_monitor_visuals, self.shared_effect, self.cycle_palette, self.override_effect_colors, self.palette_ping_pong,
                    self.delay, self.frame_rate, self.effect_hold,
                    self.palette_steps, self.speed, self.duration_factor,
                    self.time_scale, self.simulation_hold, self.auto_fit_artwork]
        for widget in controls:
            signal = "notify::active" if isinstance(widget, (Gtk.Switch, Adw.SwitchRow)) else "value-changed"
            widget.connect(signal, self._mark_dirty)
        self.font.connect("notify::font-desc", self._mark_dirty)
        self.font.connect("notify::font-desc", self._refresh_fit_warnings)
        self.per_monitor.connect("notify::active", self._refresh_fit_warnings)
        self.background.connect("notify::rgba", self._mark_dirty)
        self.background.connect("notify::rgba", self._refresh_gallery_palette)
        self.effect_preview_mode.connect("notify::selected", self._mark_dirty)
        self.effect_preview_mode.connect("notify::selected", self._mark_library_dirty)
        self.playlist_mode.connect("notify::active", self._mark_dirty)
        self.playlists_text.get_buffer().connect("changed", self._mark_dirty)
        for widget in self.effect_switches.values():
            widget.connect("toggled", self._mark_dirty)
            widget.connect("toggled", self._mark_library_dirty)
        for widget in self.monitor_spins.values():
            widget.connect("value-changed", self._mark_dirty)
        for widget in self.monitor_artwork_entries.values():
            widget.connect("changed", self._mark_dirty)
        for widget in [*self.palette_entries, *(button for buttons in self.monitor_palette_buttons.values() for button in buttons)]:
            widget.connect("notify::rgba", self._mark_dirty)
        for button in self.palette_entries:
            button.connect("notify::rgba", self._refresh_gallery_palette)
        self._monitor_signals_connected = True

    def _refresh_gallery_palette(self, *_args) -> None:
        """Use the unsaved global palette on sample-art thumbnails too."""
        if self._loading_preferences or not hasattr(self, 'effect_previews'):
            return
        config = self._preview_palette_config()
        color = palette_color_for_round(config, None, 0)
        background = config.get('background', '#000000')
        for preview in self.effect_previews.values():
            preview.set_colors(color, background)

    @staticmethod
    def _rgba_hex(button):
        rgba = button.get_rgba()
        return "#%02X%02X%02X" % tuple(
            max(0, min(255, round(ch * 255))) for ch in
            (rgba.red, rgba.green, rgba.blue))

    def _preview_palette_config(self) -> dict:
        """Use the currently selected swatches even before the user saves them.

        This configuration is used only by one-effect preview windows. It does
        not change the saved configuration or the fullscreen playback clock.
        """
        config = load_config(ctl.config_file)
        config["palette"] = [self._rgba_hex(button) for button in self.palette_entries]
        config["background"] = self._rgba_hex(self.background)
        config["cycle_palette"] = self.cycle_palette.get_active()
        override_widget = getattr(self, "override_effect_colors", None)
        config["override_effect_colors"] = (override_widget.get_active()
                                            if override_widget is not None else True)
        config["palette_ping_pong"] = (self.palette_ping_pong.get_active()
                                      if hasattr(self, "palette_ping_pong") else False)
        config["palette_steps"] = self.palette_steps.get_value_as_int()
        return config

    def _preference_snapshot(self):
        """Compare actual form values, not whether a change event occurred.

        Reverting a switch, slider, font or checkbox to its saved value must
        remove the unsaved-changes banner. The search/filter view is excluded.
        """
        buffer = self.playlists_text.get_buffer()
        playlists = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        font = self.font.get_font_desc()
        return (
            tuple(widget.get_active() for widget in (
                self.enabled, self.respect_inhibitors, self.ignore_fullscreen,
                self.per_monitor, self.per_monitor_visuals, self.shared_effect,
                self.cycle_palette, self.override_effect_colors, self.palette_ping_pong,
                self.auto_fit_artwork, self.playlist_mode)),
            tuple(widget.get_value() for widget in (
                self.delay, self.frame_rate, self.effect_hold, self.palette_steps,
                self.speed, self.duration_factor, self.time_scale, self.simulation_hold)),
            font.to_string() if font else "",
            self._rgba_hex(self.background),
            self.effect_preview_mode.get_selected(),
            tuple(self._rgba_hex(widget) for widget in self.palette_entries),
            tuple((name, self.effect_switches[name].get_active()) for name in sorted(self.effect_switches)),
            tuple((name, spin.get_value()) for name, spin in sorted(self.monitor_spins.items())),
            tuple((name, entry.get_text()) for name, entry in sorted(self.monitor_artwork_entries.items())),
            tuple((name, tuple(self._rgba_hex(b) for b in buttons))
                  for name, buttons in sorted(self.monitor_palette_buttons.items())),
            playlists,
        )

    def _mark_dirty(self, *_args):
        if self._loading_preferences:
            return
        self._pending_changes = self._preference_snapshot() != self._saved_snapshot
        gallery_active = (hasattr(self, "gallery_window")
                          and self.gallery_window.is_active())
        # The gallery owns its Save/Discard actions while it has focus.
        # Restore Preferences' own banner as soon as focus returns.
        is_dirty = self._pending_changes and not gallery_active
        self.changes_tray.set_reveal_child(is_dirty)
        self.changes_tray.set_visible(is_dirty)

    def _mark_saved(self):
        self._saved_snapshot = self._preference_snapshot()
        self._pending_changes = False
        self.changes_tray.set_reveal_child(False)
        self.changes_tray.set_visible(False)
        # Full Preferences save/discard also resets the Library's own baseline.
        if hasattr(self, "library_unsaved_banner"):
            self._library_baseline = EditBaseline(self._library_snapshot())
            self._mark_library_dirty()

    def _discard_changes(self, _button=None):
        self._load_preferences()
        self._mark_saved()
        self._set_notice("Unsaved changes discarded.")

    def _load_preferences(self) -> None:
        self._loading_preferences = True
        config = load_config(ctl.config_file)
        self.playlist_mode.set_active(bool(config.get("playlist_mode", False)))
        self.effect_preview_mode.set_selected(
            0 if config.get("effect_preview_mode", "window") == "window" else 1)
        self.library_preview_mode.set_selected(self.effect_preview_mode.get_selected())
        playlists = config.get("playlists", DEFAULT_PLAYLISTS)
        self.playlists_text.get_buffer().set_text(json.dumps(playlists, indent=2))
        self.enabled.set_active(bool(config["enabled"]))
        self.respect_inhibitors.set_active(bool(config.get("respect_inhibitors", True)))
        self.ignore_fullscreen.set_active(bool(config.get("ignore_fullscreen", True)))
        self.delay.set_value(int(config["idle_delay"]))
        self.font.set_font_desc(Pango.FontDescription.from_string(str(config["font"])))
        background_rgba = Gdk.RGBA()
        background_rgba.parse(str(config["background"]))
        self.background.set_rgba(background_rgba)
        self.frame_rate.set_value(int(config["frame_rate"]))
        self.effect_hold.set_value(float(config.get("effect_hold_seconds", 3.0)))
        excluded = set(config.get("exclude_effects", []))
        for name, widget in self.effect_switches.items():
            widget.set_active(name not in excluded)
        self.per_monitor.set_active(bool(config.get("per_monitor", False)))
        self.shared_effect.set_active(bool(config.get("shared_effect", False)))
        self.per_monitor_visuals.set_active(bool(config.get("per_monitor_visuals", False)))
        self.cycle_palette.set_active(bool(config.get("cycle_palette", True)))
        self.override_effect_colors.set_active(bool(config.get("override_effect_colors", True)))
        self.palette_ping_pong.set_active(bool(config.get("palette_ping_pong", False)))
        self.auto_fit_artwork.set_active(bool(config.get("auto_fit_artwork", True)))
        self.palette_steps.set_value(config.get("palette_steps", 12))
        self.speed.set_value(config.get("speed", 1.0))
        self.duration_factor.set_value(config.get("duration_factor", 1.0))
        self.time_scale.set_value(config.get("time_scale", 1.0))
        self.simulation_hold.set_value(config.get("simulation_hold", 1))
        self._replace_shared_palette(config.get("palette", ["#F2F2F2", "#94D2BD", "#EE9B00"]))
        for connector in self.monitor_palette_buttons:
            colors = config.get("monitor_visuals", {}).get(connector, {}).get("palette", config["palette"])
            self._replace_monitor_palette(connector, colors)
        for connector, entry in self.monitor_artwork_entries.items():
            entry.set_text(config.get("monitor_artwork", {}).get(connector, ""))
        for name, spin in self.monitor_spins.items():
            spin.set_value(config.get("monitor_fps", {}).get(name, config["frame_rate"]))
        self._update_monitor_controls()
        self._refresh_fit_warnings()
        self._loading_preferences = False
        self._refresh_watcher_control()
        self._refresh_gallery_palette()
        if hasattr(self, "_saved_snapshot"):
            self._mark_saved()

    def _reload_external_playlists(self) -> bool:
        """Refresh playlists saved by the editor window without dropping form edits.

        Never call _load_preferences here: doing so would silently overwrite
        unsaved font, color, display and timing changes in Preferences.
        """
        if self._closed or not hasattr(self, "_saved_snapshot"):
            return GLib.SOURCE_REMOVE
        raw = load_config(ctl.config_file)
        latest = json.dumps(raw.get("playlists", DEFAULT_PLAYLISTS), indent=2)
        buffer = self.playlists_text.get_buffer()
        current = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        prior = self._saved_snapshot[-1]
        if current == prior:
            self._loading_preferences = True
            try:
                buffer.set_text(latest)
            finally:
                self._loading_preferences = False
        elif latest != prior:
            self._set_notice(
                "Playlists changed in the Playlist Editor. Your unsaved raw playlist edits "
                "are still here; saving Preferences would overwrite those playlist changes.",
                error=True)
        # The stored configuration is authoritative even when there is a
        # conflict. Keep any unsaved raw edits in the form for manual review.
        baseline = list(self._saved_snapshot)
        baseline[-1] = latest
        self._saved_snapshot = tuple(baseline)
        self._mark_dirty()
        return GLib.SOURCE_REMOVE

    def _on_save(self, _button: Gtk.Button) -> None:
        buffer = self.playlists_text.get_buffer()
        raw_playlists = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        font_desc = self.font.get_font_desc()
        try:
            checked = validate_form(
                playlist_json=raw_playlists,
                playlist_enabled=self.playlist_mode.get_active(),
                font=font_desc.to_string() if font_desc else "",
                background=self._rgba_hex(self.background),
                excluded_effects=[name for name, widget in self.effect_switches.items()
                                  if not widget.get_active()],
                monitor_artwork={name: entry.get_text()
                                 for name, entry in self.monitor_artwork_entries.items()},
            )
        except ValueError as error:
            self._set_notice(str(error), error=True)
            return
        # Never replace saved maps with only today's connected displays.
        # Those monitors may be unplugged, with preferences still on disk.
        stored_monitor_settings = merge_monitor_settings(
            load_config(ctl.config_file),
            {name: spin.get_value_as_int() for name, spin in self.monitor_spins.items()},
            checked.monitor_artwork,
            {name: [self._rgba_hex(button) for button in buttons]
             for name, buttons in self.monitor_palette_buttons.items()},
        )
        try:
            ctl.update_config_values(
                {
                    "playlist_mode": self.playlist_mode.get_active(),
                    "effect_preview_mode": (
                        "window" if self.effect_preview_mode.get_selected() == 0 else "inline"),
                    "playlists": checked.playlists,
                    "enabled": self.enabled.get_active(),
                    "respect_inhibitors": self.respect_inhibitors.get_active(),
                    "ignore_fullscreen": self.ignore_fullscreen.get_active(),
                    "idle_delay": self.delay.get_value_as_int(),
                    "font": checked.font,
                    "background": checked.background,
                    "frame_rate": self.frame_rate.get_value_as_int(),
                    "effect_hold_seconds": self.effect_hold.get_value(),
                    "exclude_effects": checked.excluded_effects,
                    "per_monitor": self.per_monitor.get_active(),
                    "auto_fit_artwork": self.auto_fit_artwork.get_active(),
                    "shared_effect": (not self.per_monitor.get_active()) or self.shared_effect.get_active(),
                    "monitor_fps": stored_monitor_settings["monitor_fps"],
                    "speed": self.speed.get_value(),
                    "duration_factor": self.duration_factor.get_value(),
                    "time_scale": self.time_scale.get_value(),
                    "simulation_hold": self.simulation_hold.get_value_as_int(),
                    "cycle_palette": self.cycle_palette.get_active(),
                    "override_effect_colors": self.override_effect_colors.get_active(),
                    "palette_mode": "cycle" if self.cycle_palette.get_active() else "static",
                    "palette_ping_pong": self.palette_ping_pong.get_active(),
                    "palette_steps": self.palette_steps.get_value_as_int(),
                    "per_monitor_visuals": self.per_monitor_visuals.get_active(),
                    "palette": ["#%02X%02X%02X" % tuple(round(ch * 255) for ch in (b.get_rgba().red,b.get_rgba().green,b.get_rgba().blue)) for b in self.palette_entries],
                    "monitor_visuals": stored_monitor_settings["monitor_visuals"],
                    "monitor_artwork": stored_monitor_settings["monitor_artwork"],
                }
            )
        except (OSError, SystemExit) as error:
            self._set_notice(f"Could not save preferences: {error}", error=True)
            return
        self._mark_saved()
        self._set_notice("Saved.")
        # The dashboard belongs to this GApplication process. Update it now,
        # without waiting for the normal two-second status poll.
        app = self.get_application()
        dashboard = getattr(app, "dashboard_window", None) if app else None
        if dashboard is not None:
            dashboard._refresh_status()

