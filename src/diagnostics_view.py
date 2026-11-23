"""Standalone read-only, grouped diagnostic results window for Preferences."""
from __future__ import annotations

import threading
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk
from window_shortcuts import install_close_shortcuts
import ctl
from diagnostics_model import diagnostic_report, diagnostic_summary


class DiagnosticsWindow(Adw.Window):
    def __init__(self, parent):
        super().__init__(transient_for=parent, title="System diagnostics")
        install_close_shortcuts(self, Gtk, Gdk)
        self.set_default_size(650, 570)
        self._closed = False
        self._generation = 0
        self._checks = None
        self.connect("close-request", self._close_requested)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        # Adw.HeaderBar already supplies the native window close control.
        escape = Gtk.EventControllerKey()
        escape.connect("key-pressed", self._escape_pressed)
        self.add_controller(escape)
        self.clear_button = Gtk.Button(label="Clear")
        self.clear_button.connect("clicked", self._clear)
        header.pack_end(self.clear_button)
        self.copy_button = Gtk.Button(label="Copy results")
        self.copy_button.connect("clicked", self._copy)
        header.pack_end(self.copy_button)
        self.run_button = Gtk.Button(label="Run checks")
        self.run_button.add_css_class("suggested-action")
        self.run_button.connect("clicked", self._run)
        header.pack_end(self.run_button)
        toolbar.add_top_bar(header)

        scroller = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.body.set_margin_top(22)
        self.body.set_margin_bottom(24)
        self.body.set_margin_start(24)
        self.body.set_margin_end(24)
        self.summary = Gtk.Label(xalign=0, wrap=True)
        self.summary.add_css_class("title-3")
        self.body.append(self.summary)
        self.rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.body.append(self.rows)
        scroller.set_child(self.body)
        toolbar.set_content(scroller)
        self.set_content(toolbar)
        self._clear()
        self._run()

    def _escape_pressed(self, _controller, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _close_requested(self, *_args):
        self._closed = True
        self._generation += 1
        return False

    def _empty_rows(self):
        while child := self.rows.get_first_child():
            self.rows.remove(child)

    def _clear(self, *_args):
        # Invalidate any still-running scan so an old result cannot reappear.
        self._generation += 1
        self._checks = None
        self._empty_rows()
        self.summary.set_text("No results. Run checks to inspect this installation.")
        self.copy_button.set_sensitive(False)
        self.clear_button.set_sensitive(False)
        self.run_button.set_sensitive(True)

    def _copy(self, *_args):
        if self._checks is not None:
            self.get_clipboard().set_text(diagnostic_report(self._checks))

    def _run(self, *_args):
        if self._closed:
            return
        self._generation += 1
        generation = self._generation
        self._checks = None
        self._empty_rows()
        self.summary.set_text("Running installation checks…")
        self.run_button.set_sensitive(False)
        self.copy_button.set_sensitive(False)
        self.clear_button.set_sensitive(True)

        def worker():
            try:
                checks = ctl.collect_diagnostics()
                error = None
            except Exception as exc:  # Diagnostic errors must be visible, not crash the UI.
                checks, error = [], str(exc)
            GLib.idle_add(self._finished, generation, checks, error)

        threading.Thread(target=worker, daemon=True).start()

    def _finished(self, generation, checks, error):
        if self._closed or generation != self._generation:
            return GLib.SOURCE_REMOVE
        self.run_button.set_sensitive(True)
        self._empty_rows()
        if error is not None:
            self.summary.set_text("Diagnostics could not complete.")
            self._checks = [("Diagnostic execution", False, error)]
        else:
            self._checks = list(checks)
            self.summary.set_text(diagnostic_summary(self._checks))
        self.clear_button.set_sensitive(True)
        self.copy_button.set_sensitive(bool(self._checks))
        if self._checks:
            group = Adw.PreferencesGroup(title="Installation checks",
                                         description="Read-only checks; no settings are changed.")
            for name, ok, detail in self._checks:
                row = Adw.ActionRow(title=name, subtitle=detail)
                icon = Gtk.Image.new_from_icon_name(
                    "emblem-ok-symbolic" if ok else "dialog-warning-symbolic")
                icon.add_css_class("success" if ok else "error")
                row.add_prefix(icon)
                group.add(row)
            self.rows.append(group)
        return GLib.SOURCE_REMOVE
