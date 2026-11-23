"""Effect library lifecycle and preview process management."""
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
from palette_engine import set_vte_palette, effect_color_arguments
from playlist_engine import validate, DEFAULT_PLAYLISTS
from effect_library import select_effects
from animated_preview import AnimatedPreview, update_visible_previews
from adwaita_ui import make_group, append_action, action_row
from effect_preview_window import EffectPreviewWindow
from effect_profiles import read_records, profile
from performance_ui import PerformanceWindow
from effect_catalog import EFFECTS
from edit_state import EditBaseline, merge_saved_fields

class GalleryControllerMixin:

    def _library_snapshot(self):
        """Only settings actually editable in the Effect Library window."""
        excluded = tuple(sorted(name for name, check in self.effect_switches.items()
                                if not check.get_active()))
        mode = "window" if self.library_preview_mode.get_selected() == 0 else "inline"
        return excluded, mode

    def _mark_library_dirty(self, *_args):
        if self._loading_preferences or not hasattr(self, "_library_baseline"):
            return
        self.library_unsaved_banner.set_reveal_child(
            self._library_baseline.changed(self._library_snapshot()))

    def _save_library_changes(self, _button=None):
        """Persist only effect selections and preview mode, not other pending prefs."""
        snapshot = self._library_snapshot()
        try:
            ctl.update_config_values({"exclude_effects": list(snapshot[0]),
                                      "effect_preview_mode": snapshot[1]})
        except (OSError, ValueError, SystemExit) as error:
            self.library_toast_overlay.add_toast(Adw.Toast.new(f"Could not save library: {error}"))
            return
        self._library_baseline.commit(snapshot)
        # Preference snapshot layout: preview mode at 4, effect switches at 6.
        self._saved_snapshot = merge_saved_fields(
            self._saved_snapshot, self._preference_snapshot(), (4, 6))
        self._mark_dirty()  # Preserve dirty state of unrelated settings.
        self._mark_library_dirty()
        self.library_toast_overlay.add_toast(Adw.Toast.new("Library changes saved."))

    def _discard_library_changes(self, _button=None):
        excluded, mode = self._library_baseline.restore()
        self._loading_preferences = True
        try:
            for name, check in self.effect_switches.items():
                check.set_active(name not in excluded)
            self.library_preview_mode.set_selected(0 if mode == "window" else 1)
        finally:
            self._loading_preferences = False
        self._mark_dirty()
        self._mark_library_dirty()
        self.library_toast_overlay.add_toast(Adw.Toast.new("Library changes discarded."))




    def _queue_gallery_sync(self, *_args):
        GLib.idle_add(self._sync_gallery_previews)

    def _sync_gallery_previews(self, *_args):
        if not hasattr(self, "gallery_scroll"):
            return GLib.SOURCE_REMOVE
        # Only cards actually intersecting the scroll viewport animate.
        visible = [(self.effect_cells[name], self.effect_previews[name])
                   for name in self.effect_previews]
        return update_visible_previews(self.gallery_scroll, visible)

    def _preview_mode_changed_from_library(self, *_args):
        # Both selectors edit the same preference. Ignore redundant GTK updates.
        selected = self.library_preview_mode.get_selected()
        if self.effect_preview_mode.get_selected() != selected:
            self.effect_preview_mode.set_selected(selected)

    def _preview_mode_changed_from_settings(self, *_args):
        selected = self.effect_preview_mode.get_selected()
        if self.library_preview_mode.get_selected() != selected:
            self.library_preview_mode.set_selected(selected)

    def _gallery_activation_changed(self, *_args):
        if hasattr(self, "_saved_snapshot"):
            self._mark_dirty()
            self._mark_library_dirty()

    def _open_gallery(self, _button=None):
        for preview in self.effect_previews.values():
            preview.show_poster()
        self.gallery_window.present()
        self._mark_library_dirty()
        self._queue_gallery_sync()
        GLib.timeout_add(180, self._sync_gallery_previews)

    def _close_gallery(self, _window):
        self._stop_effect_preview()
        # Releasing all previews also drops their last RGBA textures.
        for preview in self.effect_previews.values():
            preview.release()
        self.live_preview_revealer.set_reveal_child(False)
        # The separate preview belongs to the main preferences window, not
        # to the gallery. It remains alive when the library is hidden.
        self.gallery_window.hide()
        self._mark_dirty()
        return True  # Keep the window for the next Open Library action.

    def _filter_effect_library(self, *_args) -> None:
        if getattr(self, "_library_filter_suspended", False):
            return
        duration = ("all", "short", "medium", "long")[self.library_duration.get_selected()]
        intensity = ("all", "gentle", "moderate", "energetic")[self.library_intensity.get_selected()]
        matching = select_effects(EFFECTS, self.library_search.get_text(), duration, intensity)
        # Filtering reuses the same checkbox/card objects. FlowBoxChild is a
        # wrapper created by Gtk.FlowBox.insert, so remove the wrapper, not the
        # retained card, before placing the matching cards in their original
        # catalog order. This preserves pending selection and preview state.
        while child := self.library_grid.get_first_child():
            self.library_grid.remove(child)
        for name in matching:
            self.library_grid.insert(self.effect_cells[name], -1)
        if hasattr(self, "gallery_stack"):
            self.gallery_stack.set_visible_child_name("gallery" if matching else "empty")
        self.library_count.set_text(
            f"Showing {len(matching)} of {len(EFFECTS)} effects. Filters do not change saved selections."
        )
        if hasattr(self, "gallery_scroll"):
            self._queue_gallery_sync()

    def _clear_library_filters(self, _button=None):
        """Restore the whole catalog without changing saved effect choices."""
        # A change signal fires for every selector. Avoid three unnecessary
        # FlowBox rebuilds and poster redraws during one Clear action.
        self._library_filter_suspended = True
        try:
            self.library_search.set_text("")
            self.library_duration.set_selected(0)
            self.library_intensity.set_selected(0)
        finally:
            self._library_filter_suspended = False
        self._filter_effect_library()

    def _stop_effect_preview(self, _button=None) -> None:
        """Destroy the embedded VTE widget (and its PTY child) safely."""
        self._effect_preview_generation += 1
        if self._effect_preview_cancellable is not None:
            self._effect_preview_cancellable.cancel()
            self._effect_preview_cancellable = None
        pid = self._effect_preview_pid
        self._effect_preview_pid = None
        if pid is not None:
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        terminal = self._effect_preview_terminal
        self._effect_preview_terminal = None
        if terminal is not None:
            try:
                terminal.feed_child(b"\x03")
            except (AttributeError, ValueError):
                pass
            if self.preview_area.get_child() is getattr(self, '_effect_preview_host', None):
                self.preview_area.set_child(None)
                self._effect_preview_host = None
        self.preview_title.set_text("Preview stopped")
        if hasattr(self, "live_preview_revealer"):
            self.live_preview_revealer.set_reveal_child(False)

    def _effect_preview_window_closed(self, window, *_args):
        # The window's own close-request handler stops its VTE process.
        if self._effect_preview_window is window:
            self._effect_preview_window = None
        return False

    def _reopen_effect_preview(self, _button=None) -> None:
        if self._last_preview_effect:
            self._preview_effect(None, self._last_preview_effect)

    def _preview_effect(self, _button, effect: str) -> None:
        """Play an effect in the chosen mode, independently of idle/screensaver."""
        self._last_preview_effect = effect
        self.replay_preview_button.set_sensitive(True)
        if self.effect_preview_mode.get_selected() == 0:
            self._stop_effect_preview()  # release an older inline renderer
            if self._effect_preview_window is None:
                self._effect_preview_window = EffectPreviewWindow(self)
                self._effect_preview_window.set_default_size(1100, 660)
                self._effect_preview_window.connect(
                    "close-request", self._effect_preview_window_closed)
            font = self.font.get_font_desc()
            self._effect_preview_window.play(
                effect, font.to_string() if font else "Monospace 12",
                palette_config=self._preview_palette_config())
            return
        # Inline mode remains pinned outside the scrolling gallery.
        if self._effect_preview_window is not None:
            self._effect_preview_window.close()
            self._effect_preview_window = None
        self._stop_effect_preview()
        try:
            gi.require_version("Vte", "3.91")
            from gi.repository import Vte, Gio
            binary = ctl.data_dir / "venv" / "bin" / "ttfx"
            artwork = ctl.config_dir / "logo.txt"
            if not binary.is_file() or not os.access(binary, os.X_OK):
                raise FileNotFoundError(f"Missing Rust ttfx: {binary}")
            if not artwork.is_file():
                raise FileNotFoundError(f"Missing artwork: {artwork}")
            terminal = Vte.Terminal()
            terminal.set_hexpand(False)
            terminal.set_vexpand(False)
            terminal.set_halign(Gtk.Align.CENTER)
            terminal.set_size_request(640, 240)
            terminal.set_font(self.font.get_font_desc())
            set_vte_palette(terminal, self._preview_palette_config(), Gdk)
            # VTE has an independent insertion cursor. Hide it before the
            # first frame, not just after the renderer finishes.
            terminal.feed(b"\x1b[?25l")
            # A full-width terminal aligns its text to the left even when the
            # terminal widget's halign is CENTER. Use a centred viewport child.
            host = Gtk.CenterBox(hexpand=True, vexpand=True)
            host.set_valign(Gtk.Align.CENTER)
            host.set_center_widget(terminal)
            self._effect_preview_host = host
            self.preview_area.set_child(host)
            self._effect_preview_terminal = terminal
            self.preview_title.set_text(f"Previewing {effect} with your artwork")
            self.live_preview_revealer.set_reveal_child(True)
            cancellable = Gio.Cancellable()
            self._effect_preview_cancellable = cancellable
            generation = self._effect_preview_generation

            def on_exited(_terminal, _status):
                if generation == self._effect_preview_generation:
                    self._effect_preview_pid = None
                    # The PTY has exited; keep its last painted frame visible
                    # without displaying the insertion caret.
                    terminal.feed(b"\x1b[?25l")
                    self.preview_title.set_text(f"Finished: {effect}. Choose another effect to preview.")

            def spawned(_terminal, pid, error, _data):
                if generation != self._effect_preview_generation:
                    if pid and pid > 0:
                        try:
                            os.kill(pid, signal.SIGTERM)
                        except (ProcessLookupError, PermissionError):
                            pass
                    return
                if error is not None:
                    self.preview_title.set_text(f"Could not launch {effect}: {error.message}")
                elif pid and pid > 0:
                    self._effect_preview_pid = pid

            terminal.connect("child-exited", on_exited)
            # VTE expects timeout before cancellable. Positional arguments
            # accidentally passed Gio.Cancellable as timeout ("Must be number").
            # Keep this in sync with the tested renderer launch in app.py.
            terminal.spawn_async(
                pty_flags=Vte.PtyFlags.DEFAULT,
                working_directory=str(Path.home()),
                argv=[str(binary), "-i", str(artwork), "--frame-rate", "30",
                      "--no-eol", "--no-restore-cursor",
                      "--anchor-canvas", "c", *effect_color_arguments(self._preview_palette_config()), effect],
                envv=None,
                spawn_flags=GLib.SpawnFlags.DEFAULT,
                child_setup=None,
                timeout=-1,
                cancellable=cancellable,
                callback=spawned,
                user_data=None,
            )
        except Exception as error:
            self._stop_effect_preview()
            self.preview_title.set_text(f"Preview failed for {effect}: {error}")
            self.live_preview_revealer.set_reveal_child(True)

