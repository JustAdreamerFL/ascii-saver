#!/usr/bin/env python3
"""GTK 4 control panel for ASCII Saver."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import GLib, Gio, Gtk, Adw, Gdk

import ctl
from status_model import current_status
from dashboard_playback import run_dashboard_command
from monitor_labels import playback_title, connected_displays
from adwaita_ui import make_group, action_row, append_action, compact_status_labels, set_status_labels
from app_menu import new_main_menu_button
from application_actions import ApplicationActionsMixin

from preferences_state import PreferenceStateMixin
from preferences_gallery import GalleryControllerMixin
from preferences_gallery_view import GalleryViewMixin
from preferences_displays import DisplayControllerMixin
from preferences_actions import PreferenceActionsMixin
from preferences_pages import PageBuilderMixin
from preferences_controls import PreferenceControlsMixin
from preferences_shell import ShellBuilderMixin
from window_shortcuts import install_close_shortcuts

APP_ID = "io.github.robbybobby77.AsciiSaver"


class SettingsWindow(PreferenceStateMixin, GalleryControllerMixin, GalleryViewMixin, DisplayControllerMixin, PreferenceActionsMixin, PreferenceControlsMixin, PageBuilderMixin, ShellBuilderMixin, Adw.ApplicationWindow):
    def __init__(self, application: Gtk.Application):
        super().__init__(application=application, title="ASCII Saver · Preferences")
        self._make_shell()
        install_close_shortcuts(self, Gtk, Gdk)
        self._make_common_widgets()
        self._make_gallery_cards()
        self._make_monitor_widgets()
        self._layout_preferences()
        self._make_gallery_window()
        self._make_navigation()
        self._make_raw_playlist()
        self._load_preferences()
        self._connect_dirty_signals()
        self._loading_preferences = False
        self._mark_saved()
        self._monitor_model = None
        self._monitor_handler = None
        display = Gdk.Display.get_default()
        if display is not None:
            self._monitor_model = display.get_monitors()
            self._monitor_handler = self._monitor_model.connect(
                "items-changed", self._on_display_count_changed
            )
        self._on_display_count_changed()
        # No status polling in Preferences; Dashboard owns live process state.

    def _on_display_count_changed(self, *_args):
        if self._closed:
            return
        n = self._monitor_model.get_n_items() if self._monitor_model else 0
        self.section_groups["displays"].set_description(connected_displays(n) + ". Configure each display independently if needed.")
        self._sync_monitor_widgets()
        self._refresh_fit_warnings()

    def show_section(self, name: str = "general") -> None:
        if self.sections.get_child_by_name(name) is not None:
            self.sections.set_visible_child_name(name)
        self.present()

    def _preferences_closing(self, *_args):
        self._closed = True
        if self._monitor_model is not None and self._monitor_handler is not None:
            self._monitor_model.disconnect(self._monitor_handler)
            self._monitor_handler = None
        if getattr(self, "_playlist_json_window", None) is not None:
            self._playlist_json_window.close()
            self._playlist_json_window = None
        self._stop_effect_preview()
        if self._effect_preview_window is not None:
            self._effect_preview_window.close()
            self._effect_preview_window = None
        # GTK will destroy the gallery with its parent; don't retain any
        # decoded preview textures or subprocesses in the old preferences UI.
        for preview in self.effect_previews.values():
            preview.release()
        self.gallery_window.destroy()
        self.get_application().preferences_window = None
        return False

class DashboardWindow(Adw.ApplicationWindow):
    """Small control window. Preferences are a separate adaptive window."""

    def __init__(self, application):
        super().__init__(application=application, title="ASCII Saver")
        self.set_default_size(690, 600)
        self._closed = False
        self._playback_busy = False
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)
        self.main_menu_button = new_main_menu_button()
        header.pack_end(self.main_menu_button)
        body = Adw.PreferencesPage()
        status_group = make_group("Screensaver status")
        self.renderer_status = Gtk.Label(xalign=1, selectable=True)
        self.watcher_status = Gtk.Label(xalign=1, selectable=True)
        compact_status_labels(self.renderer_status, self.watcher_status)
        action_row(status_group, "Renderer", self.renderer_status,
                   "The currently running full-screen animation or preview")
        action_row(status_group, "Idle watcher", self.watcher_status,
                   "Automatic activation service")
        # Report saved auto-launch separately from watcher process status.
        self.automatic_row, _automatic_button = append_action(
            status_group, "Automatic activation", "Configure",
            lambda _button: application.open_preferences("general"),
            "Starts on idle when enabled; independent of the manual controls below")
        body.add(status_group)
        playback = make_group("Playback", "Manual controls; automatic activation is configured in Preferences.")
        for title, label, command, subtitle in (
            ("Start on displays", "Start Now", "start", "Launch the fullscreen screensaver"),
            ("Try the effect sequence", "Preview", "preview-toggle", "Opens a resizable preview; click again to close it"),
        ):
            row, button = append_action(playback, title, label,
                                        lambda _button, c=command: self._run_command(_button, c), subtitle)
            if command == "start":
                self.start_row = row
                button.add_css_class("suggested-action")
            if command == "preview-toggle":
                self.preview_button = button
            if command == "start":
                self.start_button = button
        body.add(playback)
        navigation = make_group("Configure")
        for title, label, section in (
            ("Preferences", "Open", "general"),
            ("Tools", "Open", "tools"),
        ):
            append_action(navigation, title, label,
                          lambda _button, page=section: application.open_preferences(page))
        body.add(navigation)
        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_child(body)
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(scroller)
        toolbar.set_content(self.toast_overlay)
        self.set_content(toolbar)
        self.connect("close-request", self._dashboard_closing)
        self._monitor_model = None
        self._monitor_handler = None
        display = Gdk.Display.get_default()
        if display is not None:
            self._monitor_model = display.get_monitors()
            self._monitor_handler = self._monitor_model.connect(
                "items-changed", self._on_displays_changed
            )
        self._on_displays_changed()
        self._refresh_status()
        GLib.timeout_add_seconds(2, self._refresh_status)

    def _on_displays_changed(self, *_args):
        if self._closed:
            return
        count = self._monitor_model.get_n_items() if self._monitor_model else 0
        self.start_row.set_title(playback_title(count))
        self.start_row.set_subtitle(connected_displays(count) + ". Launch the fullscreen screensaver.")

    def _dashboard_closing(self, *_args):
        self._closed = True
        if self._monitor_model is not None and self._monitor_handler is not None:
            self._monitor_model.disconnect(self._monitor_handler)
            self._monitor_handler = None
        app = self.get_application()
        if app.preferences_window is not None:
            app.preferences_window.close()
        return False

    def _refresh_status(self):
        if self._closed:
            return GLib.SOURCE_REMOVE
        status = current_status()
        set_status_labels((self.renderer_status, self.watcher_status), (status["renderer"], status["watcher"]))
        self.automatic_row.set_subtitle(status["automatic"])
        self.preview_button.set_label("Close Preview" if status["preview"] else "Preview")
        self.preview_button.set_sensitive(
            not self._playback_busy and (not status["saver_running"] or status["preview"])
        )
        self.start_button.set_sensitive(not self._playback_busy and not status["saver_running"])
        return GLib.SOURCE_CONTINUE

    def _run_command(self, _button, command):
        if self._closed or self._playback_busy:
            return
        self._playback_busy = True
        self.start_button.set_sensitive(False)
        self.preview_button.set_sensitive(False)

        def worker():
            message = run_dashboard_command(
                command, sys.executable, Path(__file__).with_name("ctl.py"),
                ctl.is_windowed_preview,
            )
            def update():
                self._playback_busy = False
                if not self._closed:
                    self.toast_overlay.add_toast(Adw.Toast.new(message[:180]))
                    self._refresh_status()
                return GLib.SOURCE_REMOVE
            GLib.idle_add(update)
        threading.Thread(target=worker, daemon=True).start()

class SettingsApplication(ApplicationActionsMixin, Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.dashboard_window = None
        self.preferences_window = None
        self.playlist_window = None
        self._install_menu_actions()

    def do_activate(self) -> None:
        if self.dashboard_window is None:
            self.dashboard_window = DashboardWindow(self)
        self.dashboard_window.present()

    def do_command_line(self, command_line):
        args = set(command_line.get_arguments()[1:])
        if "--preferences" in args:
            self.open_preferences("general")
        elif "--playlist-editor" in args:
            self.open_playlist_editor()
        else:
            self.activate()
        return 0

    def open_preferences(self, name="general", *, open_library=False, open_playlist=False):
        if self.preferences_window is None:
            self.preferences_window = SettingsWindow(self)
        self.preferences_window.show_section(name)
        if open_library:
            self.preferences_window._open_gallery()
        if open_playlist:
            self.preferences_window._open_playlist_editor(None)


def main() -> int:
    Adw.init()
    return SettingsApplication().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
