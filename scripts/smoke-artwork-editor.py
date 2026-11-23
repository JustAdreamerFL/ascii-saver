#!/usr/bin/env python3
"""Optional manual UI check on a system with GTK4/libadwaita installed.

Opens a temporary test artwork (not the user's configuration). Closing or
saving only affects that temporary file. It is safe to run before installation.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio
from artwork_editor import ArtworkEditor

class SmokeApp(Adw.Application):
    def do_activate(self):
        self.main_window = Adw.ApplicationWindow(application=self, title='Artwork Editor Smoke Test')
        self.main_window.set_default_size(240, 140)
        self.main_window.present()
        self.editor = ArtworkEditor(self.main_window, file_path)
        self.editor.present()

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / 'example.txt'
        file_path.write_text('  ***\n *** ***\n  ***\n', encoding='utf-8')
        app = SmokeApp(application_id='io.github.robbybobby77.AsciiSaver.EditorSmoke',
                       flags=Gio.ApplicationFlags.NON_UNIQUE)
        sys.exit(app.run(['smoke-artwork-editor']))
