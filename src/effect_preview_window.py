"""Non-modal, single-process ttfx effect preview used by the playlist editor.

The image/card itself selects the effect. The dedicated Play button launches
this separate window so the playlist editor never loses its scroll space.
"""
from __future__ import annotations

import os
import signal
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib, Gio, Pango, Adw, Gdk
from window_shortcuts import install_close_shortcuts

import ctl
from helpers import load_config
from palette_engine import set_vte_palette, effect_color_arguments


class EffectPreviewWindow(Adw.Window):
    def __init__(self, parent: Gtk.Window):
        super().__init__(title='ASCII Saver · Effect preview', transient_for=parent)
        install_close_shortcuts(self, Gtk, Gdk)
        self.set_default_size(1100, 660)
        self.set_resizable(True)
        self._cancellable = None
        self._pid = None
        self._generation = 0
        self._terminal = None
        self._last_play = None

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for setter in (root.set_margin_top, root.set_margin_bottom,
                       root.set_margin_start, root.set_margin_end):
            setter(10)
        # Native header only: the titlebar already supplies a Close button.
        # Replay is kept *in* the preview so it is useful after an effect ends.
        self.title_label = Gtk.Label(label='Effect preview', xalign=0)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        replay = Gtk.Button(label='Replay')
        replay.set_tooltip_text('Run the same effect again')
        replay.set_sensitive(False)
        replay.connect('clicked', self._replay)
        self.replay_button = replay

        self.terminal_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.terminal_area.set_vexpand(True)
        root.append(self.terminal_area)
        header = Adw.HeaderBar()
        header.set_title_widget(self.title_label)
        header.pack_end(replay)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(root)
        self.set_content(toolbar)
        self.connect('close-request', self._close_requested)

    def _stop(self):
        self._generation += 1
        if self._cancellable is not None:
            self._cancellable.cancel()
            self._cancellable = None
        if self._pid is not None:
            try:
                os.kill(self._pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            self._pid = None
        if self._terminal is not None:
            if self._terminal.get_parent() is self.terminal_area:
                self.terminal_area.remove(self._terminal)
            self._terminal = None

    def _close_requested(self, *_args):
        self._stop()
        return False  # Destroy the window, no hidden PTY/renderer retained.

    def _replay(self, _button=None):
        if self._last_play is not None:
            effect, font_name, palette_config = self._last_play
            self.play(effect, font_name, palette_config)

    def play(self, effect: str, font_name: str = 'Monospace 12',
             palette_config: dict | None = None):
        self._stop()
        self._last_play = (effect, font_name, palette_config)
        self.replay_button.set_sensitive(True)
        self.title_label.set_text(effect)
        self.present()
        try:
            gi.require_version('Vte', '3.91')
            from gi.repository import Vte
            binary = ctl.data_dir / 'venv' / 'bin' / 'ttfx'
            artwork = ctl.config_dir / 'logo.txt'
            if not (binary.is_file() and os.access(binary, os.X_OK)):
                raise FileNotFoundError(f'Rust renderer unavailable: {binary}')
            if not artwork.is_file():
                raise FileNotFoundError(f'Artwork unavailable: {artwork}')
            terminal = Vte.Terminal()
            terminal.set_hexpand(True)
            terminal.set_vexpand(True)
            terminal.set_font(Pango.FontDescription.from_string(font_name))
            config = palette_config if palette_config is not None else load_config(ctl.config_file)
            set_vte_palette(terminal, config, Gdk)
            terminal.feed(b"\x1b[?25l")
            self._terminal = terminal
            self.terminal_area.append(terminal)
            generation = self._generation
            cancellable = Gio.Cancellable()
            self._cancellable = cancellable

            def spawned(_terminal, pid, error, _data):
                if generation != self._generation:
                    if pid and pid > 0:
                        try:
                            os.kill(pid, signal.SIGTERM)
                        except (ProcessLookupError, PermissionError):
                            pass
                    return
                if error is not None:
                    self.title_label.set_text(f'Preview launch failed: {error.message}')
                else:
                    self._pid = pid

            def exited(_terminal, _status):
                if generation == self._generation:
                    self._pid = None
                    terminal.feed(b"\x1b[?25l")
                    self.title_label.set_text(f'{effect} · Finished')

            terminal.connect('child-exited', exited)
            terminal.spawn_async(
                pty_flags=Vte.PtyFlags.DEFAULT,
                working_directory=str(Path.home()),
                argv=[str(binary), '-i', str(artwork), '--frame-rate', '30',
                      '--no-eol', '--no-restore-cursor',
                      '--anchor-canvas', 'c', *effect_color_arguments(config), effect],
                envv=None, spawn_flags=GLib.SpawnFlags.DEFAULT,
                child_setup=None, timeout=-1,
                cancellable=cancellable, callback=spawned, user_data=None,
            )
        except (OSError, ValueError, GLib.Error) as exc:
            self._stop()
            self.title_label.set_text(f'Could not preview {effect}: {exc}')
