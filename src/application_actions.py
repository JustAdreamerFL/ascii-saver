"""Application-wide GActions, HIG accelerators and menu routing."""
from __future__ import annotations
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio
from app_menu import show_about, show_shortcuts, show_help, show_components


class ApplicationActionsMixin:
    def _install_menu_actions(self):
        actions = {
            'preferences': lambda: self.open_preferences('general'),
            'shortcuts': lambda: show_shortcuts(self._parent_window()),
            'help': lambda: show_help(self._parent_window()),
            'about': lambda: show_about(self._parent_window()),
            'components': lambda: show_components(self._parent_window()),
            'edit-artwork': self._edit_default_artwork,
            'performance': self._open_performance,
            'measurements': self._open_measurements,
            'diagnostics': self._open_diagnostics,
            'quit': self.quit,
            'close-window': self._close_active_window,
            'menu': self._open_primary_menu,
        }
        for name, handler in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect('activate', lambda _action, _param, callback=handler: callback())
            self.add_action(action)
        for name, keys in {
            'preferences': ['<Primary>comma'],
            'shortcuts': ['<Primary>question', '<Primary><Shift>slash'],
            'help': ['F1'],
            'quit': ['<Primary>q'],
            'close-window': ['<Primary>w'],
            'menu': ['F10'],
        }.items():
            self.set_accels_for_action('app.' + name, keys)

    def _parent_window(self):
        return self.get_active_window() or self.dashboard_window

    def _close_active_window(self):
        win = self.get_active_window()
        if win is not None:
            win.close()

    def _open_primary_menu(self):
        if self.dashboard_window is None:
            self.activate()
        self.dashboard_window.present()
        self.dashboard_window.main_menu_button.popup()

    def open_playlist_editor(self):
        # Reuse a native application window instead of a second process with
        # a distinct .Playlists app ID. A real toplevel can be represented by
        # KDE Task Manager, and inherits this application's desktop identity.
        if self.playlist_window is None:
            from playlist_editor import Editor
            self.playlist_window = Editor(self)
            self.playlist_window.connect("close-request", self._playlist_editor_closed)
        self.playlist_window.present()

    def _playlist_editor_closed(self, *_args):
        self.playlist_window = None
        if self.preferences_window is not None:
            self.preferences_window._reload_external_playlists()
        return False


    def _edit_default_artwork(self):
        # Keep a single editor implementation, including its unsaved guard.
        self.open_preferences('appearance')
        self.preferences_window._edit_default_artwork()

    def _open_performance(self):
        import os
        from pathlib import Path
        from performance_ui import PerformanceWindow
        cache = Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache')))
        window = PerformanceWindow(cache / 'ascii-saver' / 'performance.jsonl')
        window.set_transient_for(self._parent_window())
        window.present()

    def _open_measurements(self):
        import os
        from pathlib import Path
        from effect_profiles import read_records, profile
        from measurements_ui import build_window
        cache = Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))) / 'ascii-saver'
        labels = (self.preferences_window.monitor_labels
                  if self.preferences_window is not None else {})
        window = build_window(self._parent_window(), profile(read_records(cache), min_runs=1), labels)
        window.present()

    def _open_diagnostics(self):
        from diagnostics_view import DiagnosticsWindow
        window = DiagnosticsWindow(self._parent_window())
        window.present()
