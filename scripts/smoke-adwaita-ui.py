#!/usr/bin/env python3
"""Launch-free settings widget construction check for an actual GTK4 desktop.

Run from the extracted source on the target CachyOS desktop:
    python scripts/smoke-adwaita-ui.py

Requires a graphical session, gtk4, libadwaita and PyGObject. It does not
write preferences or launch the fullscreen renderer. Useful for catching
missing GI methods/property mismatches not testable in an offline container.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, Adw

from settings import SettingsWindow, DashboardWindow
from component_versions import collect_versions


def main():
    Adw.init()
    app = Adw.Application(
        application_id="io.github.robbybobby77.AsciiSaver.UISmoke",
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )
    app.register(None)
    app.preferences_window = None
    window = SettingsWindow(app)
    try:
        assert isinstance(window, Adw.ApplicationWindow)
        for name in ("general", "appearance", "displays", "animations", "preview"):
            page = window._page_boxes[name]
            assert isinstance(page, Adw.PreferencesPage)
            window.sections.set_visible_child_name(name)
            assert window.sections.get_visible_child_name() == name
        assert isinstance(window.gallery_window, Adw.Window)
        for field in ("enabled", "respect_inhibitors", "ignore_fullscreen", "per_monitor", "cycle_palette", "playlist_mode"):
            assert isinstance(getattr(window, field), Adw.SwitchRow), field
        assert isinstance(window.toast_overlay, Adw.ToastOverlay)
        assert isinstance(window.unsaved_banner, Gtk.Revealer)
        dashboard = DashboardWindow(app)
        try:
            assert dashboard.main_menu_button.get_menu_model() is not None
            assert isinstance(collect_versions(), dict)
        finally:
            dashboard.close()
        print("PASS: Adwaita pages, library, dashboard main menu and component status constructed")
    finally:
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
