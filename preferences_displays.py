"""Monitor controls and text geometry diagnostics."""
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

class DisplayControllerMixin:
    def _refresh_fit_warnings(self, *_args):
        """Display per-monitor fit estimates, including mode and chosen art."""
        from artwork_fit import artwork_cells, choose_artwork_font_sizes
        try:
            desc = self.font.get_font_desc()
            if not desc or desc.get_size() <= 0:
                return
            layout = self.create_pango_layout("M")
            layout.set_font_description(desc)
            glyph_w, glyph_h = layout.get_pixel_size()
            if not glyph_w or not glyph_h:
                return
            display = Gdk.Display.get_default()
            monitors = display.get_monitors() if display else None
            if not monitors:
                return
            own_base = ctl.config_dir.resolve()
            capacities = {}
            artwork_by_monitor = {}
            statuses = []
            for index in range(monitors.get_n_items()):
                mon = monitors.get_item(index)
                key = mon.get_connector() or mon.get_model() or f"Monitor-{index + 1}"
                rect = mon.get_geometry()
                capacities[key] = (max(1, (rect.width - 24) // glyph_w),
                                   max(1, (rect.height - 24) // glyph_h))
                selected = self.monitor_artwork_entries.get(key)
                relative = selected.get_text() if selected and self.per_monitor.get_active() else "logo.txt"
                path = (own_base / (relative or "logo.txt")).resolve()
                if not path.is_relative_to(own_base) or not path.is_file():
                    path = own_base / "logo.txt"
                try:
                    artwork_by_monitor[key] = artwork_cells(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeError):
                    artwork_by_monitor[key] = (0, 0)
            independent = self.per_monitor.get_active()
            fit_on = self.auto_fit_artwork.get_active()
            base_size = desc.get_size() / Pango.SCALE
            proposed = choose_artwork_font_sizes(
                base_size, artwork_by_monitor, capacities,
                auto_fit=fit_on, independent=independent,
            )
            for index in range(monitors.get_n_items()):
                mon = monitors.get_item(index)
                key = mon.get_connector() or mon.get_model() or f"Monitor-{index+1}"
                artwork_cells_current = artwork_by_monitor[key]
                new_size = proposed.get(key, base_size)
                cols, rows = capacities[key]
                if not all(artwork_cells_current):
                    detail = "artwork unavailable"
                elif not fit_on:
                    clipped = artwork_cells_current[0] > cols or artwork_cells_current[1] > rows
                    detail = "no fitting; may clip" if clipped else "no fitting needed"
                elif new_size < base_size:
                    detail = f"fit to about {new_size:g} pt"
                else:
                    detail = "fits at configured font size"
                statuses.append(f"{mon.get_model() or key}: {detail}")
            mode = "per display" if independent else "shared (smallest display)"
            self.fit_notice.set_text(f"Artwork fit: {mode}. " + "  |  ".join(statuses))
        except (OSError, UnicodeError, AttributeError, ValueError) as error:
            self.fit_notice.set_text(f"Fit estimate unavailable: {error}")

    def _update_monitor_controls(self, *_args):
        independent = self.per_monitor.get_active()
        own_palette = self.per_monitor_visuals.get_active()
        self.monitor_revealer.set_reveal_child(independent or own_palette)
        self.monitor_rates_group.set_visible(independent)
        self.monitor_artwork_group.set_visible(independent)
        self.monitor_options_group.set_visible(independent)
        self.monitor_colors_group.set_visible(own_palette)
        self.global_fps_label.set_visible(not independent)
        self.frame_rate.set_visible(not independent)
        # Shared colors remain the fallback for previews and new displays.
        self.shared_palette_label.set_visible(True)
        self.shared_palette_widget.set_visible(True)

