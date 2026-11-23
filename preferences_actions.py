"""Nonblocking app actions and diagnostics windows."""
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
from status_model import current_status
from helpers import load_config, valid_color
from playlist_engine import validate, DEFAULT_PLAYLISTS
from effect_library import select_effects
from animated_preview import update_visible_previews
from effect_preview_window import EffectPreviewWindow
from effect_profiles import read_records, profile
from performance_ui import PerformanceWindow
from effect_catalog import EFFECTS

class PreferenceActionsMixin:
    def _edit_default_artwork(self, _button=None) -> None:
        """Open a real Adwaita text editor, never a terminal editor in a pipe.

        Running `ctl.py edit` with captured stdout can turn Vim/Nano escape
        sequences into literal text in the preferences window. Keep the edit
        interaction inside GTK instead and reuse the monitor artwork editor.
        """
        from artwork_editor import ArtworkEditor

        path = ctl.config_dir / "logo.txt"
        if not path.is_file():
            self._set_notice("Artwork file not found.", error=True)
            return
        existing = getattr(self, "_default_artwork_editor", None)
        if existing is not None:
            existing.present()
            return
        def finished(message):
            # Report completion only when the editor actually closes.
            self._default_artwork_editor = None
            self._set_notice(message)

        try:
            editor = ArtworkEditor(self, path, on_finished=finished, config_dir=ctl.config_dir)
        except (OSError, UnicodeError) as error:
            self._set_notice(f"Cannot open artwork: {error}", error=True)
            return
        self._default_artwork_editor = editor
        editor.present()

    def _open_playlist_editor(self, _button):
        # A separate GApplication ID creates a separate Wayland application and
        # the generic taskbar entry reported on KDE. Keep this a real toplevel,
        # but use the same Gtk.Application as the dashboard and Preferences.
        self.get_application().open_playlist_editor()

    def _open_duration_profiles(self, _button):
        from measurements_ui import build_window
        cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home()/".cache"))) / "ascii-saver"
        rows = profile(read_records(cache), min_runs=1)
        window = build_window(self, rows, self.monitor_labels)
        self.duration_window = window
        window.present()

    def _open_performance(self, _button):
        cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home()/".cache")))
        window = PerformanceWindow(cache / "ascii-saver" / "performance.jsonl")
        window.set_transient_for(self)
        window.present()

    def _refresh_status(self) -> bool:
        # Live process status is shown and refreshed by the Dashboard only.
        return GLib.SOURCE_REMOVE

    def _set_notice(self, message: str, error: bool = False) -> None:
        # Avoid permanent success/error rows that fill Preferences with state.
        # Keep longer failures accessible instead of silently dropping them.
        text = message.strip() or ("Action failed" if error else "Done")
        toast = Adw.Toast.new(text[:350])
        self.toast_overlay.add_toast(toast)

    def _open_diagnostics(self, _button=None):
        from diagnostics_view import DiagnosticsWindow
        existing = getattr(self, "_diagnostics_window", None)
        if existing is not None:
            existing.present()
            return
        window = DiagnosticsWindow(self)
        self._diagnostics_window = window
        window.connect("close-request", self._diagnostics_closed)
        window.present()

    def _diagnostics_closed(self, *_args):
        self._diagnostics_window = None
        return False

    def _on_command(self, _button: Gtk.Button, command: str) -> None:
        if command == "edit":
            self._edit_default_artwork(_button)
            return
        if command == "doctor":
            self._open_diagnostics(_button)
            return
        self._set_notice(f"Running {command}…")

        def worker() -> None:
            try:
                completed = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve().with_name("ctl.py")), command],
                    text=True,
                    capture_output=True,
                    check=False,
                    env=os.environ.copy(),
                )
            except OSError as error:
                GLib.idle_add(self._command_finished, str(error), True)
                return
            output = (completed.stdout or completed.stderr).strip()
            if not output:
                output = (
                    f"{command} completed" if completed.returncode == 0 else f"{command} failed"
                )
            GLib.idle_add(
                self._command_finished,
                output,
                completed.returncode != 0,
            )

        threading.Thread(target=worker, daemon=True).start()

    def _command_finished(self, output: str, failed: bool) -> bool:
        self._set_notice(output, error=failed)
        self._refresh_status()
        return GLib.SOURCE_REMOVE

