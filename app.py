#!/usr/bin/env python3
"""Fullscreen GTK/VTE renderer for ASCII Saver."""

from __future__ import annotations

import argparse
import os
import signal
import sys
from pathlib import Path
from frame_report import parse_frame_report
import time
from performance_logger import ProcessSampler, JsonlRecorder
from effect_timing import BoundedLog
from screen_lock_backend import GNOME, select_screen_lock_backend
from gnome_cursor_bridge import FullscreenCursorLease

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Vte", "3.91")
try:
    # Load the Layer Shell namespace before GTK realizes a Wayland surface.
    gi.require_version("Gtk4LayerShell", "1.0")
    _LAYER_SHELL_AVAILABLE = True
except ValueError:
    _LAYER_SHELL_AVAILABLE = False
if _LAYER_SHELL_AVAILABLE:
    from gi.repository import Gtk4LayerShell  # type: ignore[attr-defined]  # noqa: E402
else:
    Gtk4LayerShell = None
from gi.repository import Gdk, Gio, GLib, Gtk, Pango, Vte, Adw  # noqa: E402

from playlist_engine import Scheduler, DEFAULT_PLAYLISTS, EFFECTS
from effect_rotation import EffectShuffleBag
from preview_sequence import PreviewSequence
from effect_selection import select_effect, effect_args
from artwork_fit import artwork_cells, choose_artwork_font_sizes
from palette_engine import palette_color_for_round, effect_color_arguments

from helpers import (  # noqa: E402
    TTE_MAX_FAILURES,
    TTE_SUCCESS_RESTART_MS,
    load_config,
    pid_file_path,
    read_version,
    runtime_dir,
    tte_exit_ok,
    tte_failure_delay_ms,
    write_pid_file,
)


APP_ID = "io.github.robbybobby77.AsciiSaver"
VERSION = read_version()


def xdg_path(env_name: str, fallback: Path) -> Path:
    value = os.environ.get(env_name)
    return Path(value).expanduser() if value else fallback


CONFIG_DIR = Path(
    os.environ.get(
        "ASCII_SAVER_CONFIG_DIR",
        xdg_path("XDG_CONFIG_HOME", Path.home() / ".config") / "ascii-saver",
    )
)
DATA_DIR = Path(
    os.environ.get(
        "ASCII_SAVER_DATA_DIR",
        xdg_path("XDG_DATA_HOME", Path.home() / ".local" / "share") / "ascii-saver",
    )
)


def parse_color(value: str, fallback: str) -> Gdk.RGBA:
    color = Gdk.RGBA()
    if not color.parse(value):
        color.parse(fallback)
    return color


class SaverWindow(Adw.ApplicationWindow):
    def __init__(
        self,
        app: "SaverApplication",
        monitor: Gdk.Monitor | None,
        windowed: bool,
        keyboard_surface: bool = False,
        defer_start: bool = False,
    ):
        super().__init__(application=app, title="ASCII Saver")
        self.app = app
        self.monitor = monitor
        self.windowed = windowed
        self.armed = False
        self.running = False
        self.closing = False
        self.tte_failures = 0
        self.palette_tick = 0
        # A monitor owns its unordered playback history. Never share it with
        # other displays or the persistent windowed preview.
        self._effect_bag = EffectShuffleBag()
        self.monitor_id = (monitor.get_connector() or monitor.get_model() or "Unknown") if monitor is not None else "default"
        self.cancellable = Gio.Cancellable()
        self.child_pid = None
        self.effect_label = "unknown"
        self.effect_started = None
        self.set_decorated(windowed)
        self.set_resizable(True)
        if windowed:
            self.set_title("ASCII Saver · Preview")

        self.terminal = Vte.Terminal()
        self.terminal.set_hexpand(True)
        self.terminal.set_vexpand(True)
        self.terminal.set_font(Pango.FontDescription.from_string(str(app.config["font"])))
        self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.OFF)
        self.terminal.set_cursor_shape(Vte.CursorShape.BLOCK)
        # Keep VTE's insertion cursor hidden before the child has emitted a
        # first frame and after it exits. Renderer suppresses cursor restore.
        self.terminal.feed(b"\x1b[?25l")
        background = parse_color(str(app.config["background"]), "#000000")
        foreground = parse_color("#f2f2f2", "#ffffff")
        self.terminal.set_colors(foreground, background, [])
        self.terminal.connect("child-exited", self._on_child_exited)

        # GTK cursor settings on a VTE widget are not sufficient on GNOME:
        # VTE replaces the invisible pointer with an I-beam over its text.
        # An input-capable, visually transparent child above VTE owns pointer
        # hit-testing and applies our invisible cursor instead. It must cover
        # the *entire* fullscreen surface and never intercept windowed preview.
        # This uses public GTK4 APIs, without a GNOME Shell extension.
        self.cursor_overlay = None
        self.cursor_catcher = None
        if windowed:
            toolbar = Adw.ToolbarView()
            toolbar.add_top_bar(Adw.HeaderBar())
            toolbar.set_content(self.terminal)
            self.set_content(toolbar)
        else:
            self.cursor_overlay = Gtk.Overlay()
            self.cursor_overlay.set_hexpand(True)
            self.cursor_overlay.set_vexpand(True)
            self.cursor_overlay.set_child(self.terminal)
            self.cursor_catcher = Gtk.DrawingArea()
            self.cursor_catcher.set_hexpand(True)
            self.cursor_catcher.set_vexpand(True)
            self.cursor_catcher.set_halign(Gtk.Align.FILL)
            self.cursor_catcher.set_valign(Gtk.Align.FILL)
            self.cursor_catcher.set_can_target(True)
            self.cursor_catcher.set_can_focus(False)
            self.cursor_overlay.add_overlay(self.cursor_catcher)
            self.set_content(self.cursor_overlay)

        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._dismiss)
        key.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.add_controller(key)
        motion = Gtk.EventControllerMotion()
        # Enter is not motion: the pointer may already be visible when the
        # fullscreen surface appears, or enter without a motion event.
        motion.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        motion.connect("enter", self._on_pointer_enter)
        motion.connect("motion", self._dismiss)
        self.add_controller(motion)
        click = Gtk.GestureClick()
        click.connect("pressed", self._dismiss)
        self.add_controller(click)
        scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll.connect("scroll", self._dismiss)
        self.add_controller(scroll)

        if windowed:
            self.set_default_size(1000, 700)
        elif app.layer_shell:
            Gtk4LayerShell.init_for_window(self)
            Gtk4LayerShell.set_namespace(self, "ascii-saver")
            Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.OVERLAY)
            Gtk4LayerShell.set_monitor(self, monitor)
            for edge in (
                Gtk4LayerShell.Edge.LEFT,
                Gtk4LayerShell.Edge.RIGHT,
                Gtk4LayerShell.Edge.TOP,
                Gtk4LayerShell.Edge.BOTTOM,
            ):
                Gtk4LayerShell.set_anchor(self, edge, True)
            Gtk4LayerShell.set_exclusive_zone(self, -1)
            keyboard_mode = (
                Gtk4LayerShell.KeyboardMode.EXCLUSIVE
                if keyboard_surface
                else Gtk4LayerShell.KeyboardMode.NONE
            )
            Gtk4LayerShell.set_keyboard_mode(self, keyboard_mode)
        elif monitor is not None:
            self.fullscreen_on_monitor(monitor)
        else:
            self.fullscreen()

        self.connect("close-request", self._on_close)
        if not windowed:
            # Connect BEFORE present(): otherwise a fast compositor can map the
            # surface before this callback exists. Also cover re-realization.
            self.connect("realize", self._on_mapped_for_cursor)
            self.connect("map", self._on_mapped_for_cursor)
            self.terminal.connect("realize", self._on_mapped_for_cursor)
            self._hide_cursor()
        self.present()
        if not windowed:
            # Cover the already-realized case without relying on a timer.
            self._hide_cursor()
        # Fullscreen windows join a monitor cohort; do not let independently
        # queued per-window timers drift across synchronization rounds.
        if not defer_start:
            GLib.timeout_add(350, self._start)
        GLib.idle_add(self._arm)

    def _on_pointer_enter(self, *_args) -> None:
        # In Wayland, the compositor changes the cursor only for the surface
        # under the pointer. Reassert when the pointer enters our surface.
        self._hide_cursor()

    def _on_mapped_for_cursor(self, *_args) -> None:
        self._hide_cursor()
        # GNOME Shell can own the pointer above our normal fullscreen surface.
        # Advertise presence only after mapping, never for windowed previews.
        self.app._announce_cursor_lease()

    def _hide_cursor(self) -> None:
        if self.windowed:
            return
        if not hasattr(self, "_invisible_cursor"):
            # "none" is the documented cross-platform GTK4 cursor name.
            # A transparent texture is only a fallback for unsupported themes.
            invisible = Gdk.Cursor.new_from_name("none", None)
            if invisible is None:
                pixels = GLib.Bytes.new(bytes((0, 0, 0, 0)))
                texture = Gdk.MemoryTexture.new(1, 1, Gdk.MemoryFormat.R8G8B8A8, pixels, 4)
                invisible = Gdk.Cursor.new_from_texture(texture, 0, 0, None)
            self._invisible_cursor = invisible
        self.set_cursor(self._invisible_cursor)
        self.terminal.set_cursor(self._invisible_cursor)
        # The catcher must explicitly own the pointer cursor, rather than
        # inheriting VTE's text-select cursor. Reapply on mapping and entering.
        if self.cursor_overlay is not None:
            self.cursor_overlay.set_cursor(self._invisible_cursor)
        if self.cursor_catcher is not None:
            self.cursor_catcher.set_cursor(self._invisible_cursor)
        surface = self.get_surface()
        if surface is not None:
            surface.set_cursor(self._invisible_cursor)
            # Cover a pointer-specific cursor overriding the default surface
            # cursor, without grabbing or warping the user's pointer.
            display = self.get_display()
            seat = display.get_default_seat() if display is not None else None
            pointer = seat.get_pointer() if seat is not None else None
            if pointer is not None:
                surface.set_device_cursor(pointer, self._invisible_cursor)

    def _arm(self) -> bool:
        self.armed = True
        return GLib.SOURCE_REMOVE

    def _dismiss(self, *_args):
        if self.windowed:
            # Preview stays open on ordinary input. Motion, click and scroll
            # controllers call this method with *different* argument shapes.
            # Do not interpret their X coordinate/press count as a keyval.
            if not _args or not isinstance(_args[0], Gtk.EventControllerKey):
                return False
            keyval = _args[1]
            state = _args[3]
            name = (Gdk.keyval_name(keyval) or "").lower()
            ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
            if name == "escape" or (ctrl and name in ("w", "q")):
                self.close()
                return True
            return False
        if self.armed:
            self.app.quit_saver()
        return True

    def _on_close(self, *_args):
        self.app.quit_saver()
        return False

    def _artwork_path(self) -> Path:
        artwork = CONFIG_DIR / "logo.txt"
        selected = self.app.config.get("monitor_artwork", {}).get(self.monitor_id)
        if self.app.config.get("per_monitor_visuals") and isinstance(selected, str):
            # Do not allow custom artwork paths to escape the user's config dir.
            candidate = (CONFIG_DIR / selected).resolve()
            if candidate.is_relative_to(CONFIG_DIR.resolve()) and candidate.is_file():
                artwork = candidate
        return artwork

    def _auto_fit_monitor_artwork(self) -> None:
        """Fit the actual artwork, never using a previous effect's font size.

        Independent mode fits only this monitor. Shared mode fits the common
        artwork to the narrowest active display, then uses that same font on
        all displays. The user-configured size remains untouched.
        """
        desc = Pango.FontDescription.from_string(str(self.app.config["font"]))
        self.terminal.set_font(desc)
        if not self.app.config.get("auto_fit_artwork", True) or self.monitor is None:
            return
        base_size = desc.get_size() / Pango.SCALE
        if base_size <= 0:
            return
        try:
            art = artwork_cells(self.current_artwork_path.read_text(encoding="utf-8"))
            if not all(art):
                return
            # Read baseline VTE glyph metrics *after* restoring the configured
            # font. Never derive capacities from an already-shrunk terminal.
            glyph_w = self.terminal.get_char_width()
            glyph_h = self.terminal.get_char_height()
            if glyph_w <= 0 or glyph_h <= 0:
                return
            independent = bool(self.app.config.get("per_monitor", False))
            monitors = [self.monitor]
            if not independent and self.app._monitors is not None:
                monitors = [
                    self.app._monitors.get_item(i)
                    for i in range(self.app._monitors.get_n_items())
                ] or monitors
            capacities = {}
            artwork_by_monitor = {}
            for monitor in monitors:
                key = monitor.get_connector() or monitor.get_model() or "unknown"
                rect = monitor.get_geometry()
                # Layout geometry is per-monitor, not the VTE cell grid shared
                # by whichever window last happened to run an effect.
                capacities[key] = (max(1, (rect.width - 24) // glyph_w),
                                   max(1, (rect.height - 24) // glyph_h))
                artwork_by_monitor[key] = art
            own_key = self.monitor.get_connector() or self.monitor.get_model() or "unknown"
            sizes = choose_artwork_font_sizes(
                base_size, artwork_by_monitor, capacities,
                auto_fit=True, independent=independent,
            )
            desired = sizes.get(own_key, base_size)
            if desired < base_size:
                desc.set_size(round(desired * Pango.SCALE))
                self.terminal.set_font(desc)
                print(f"ascii-saver: {self.monitor_id}: font fit {base_size:g} -> "
                      f"{desired:g} pt", file=sys.stderr)
        except (OSError, UnicodeError, AttributeError, ValueError) as error:
            print(f"ascii-saver: cannot estimate artwork fit: {error}", file=sys.stderr)

    def _tte_argv(self) -> list[str]:
        executable = Path(os.environ.get("ASCII_SAVER_TTFX", DATA_DIR / "venv" / "bin" / "ttfx"))
        if not executable.exists():
            executable = Path("ttfx")
        background = str(self.app.config["background"]).lstrip("#")
        # Fullscreen monitors advance in the *same* synchronization round.
        # Retries must reuse its color, and preview must have a separate clock.
        palette_round = self.palette_tick if self.windowed else self.app.shared_round
        text_color = palette_color_for_round(
            self.app.config, None if self.windowed else self.monitor_id, palette_round,
        )
        self.terminal.set_colors(parse_color(text_color, "#f2f2f2"), parse_color(self.app.config["background"], "#000000"), [])
        artwork = self._artwork_path()
        fps = self.app.config["frame_rate"]
        if self.app.config.get("per_monitor") and self.monitor is not None:
            connector = self.monitor.get_connector() or self.monitor.get_model() or "Unknown"
            fps = self.app.config.get("monitor_fps", {}).get(connector, fps)
        # A configured FPS limit is a playback target, not measured GPU frames.
        # Keep the effective cap for accurate per-effect diagnostics.
        self.effective_fps_cap = max(1, min(240, round(fps * float(self.app.config.get("speed", 1.0)))))
        # Two deliberately distinct controls: legacy FPS pacing, or explicit
        # per-frame dwell. Neither drops simulation steps. The latter changes
        # wall-clock duration but necessarily changes output FPS as well.
        duration_factor = float(self.app.config.get("duration_factor", 1.0))
        duration_factor = max(0.5, min(10.0, duration_factor))
        argv = [
            str(executable),
            "-i",
            str(artwork),
            "--frame-rate",
            str(self.effective_fps_cap),
            "--duration-factor", str(duration_factor),
            "--time-scale", str(self.app.config.get("time_scale", 1.0)),
            "--simulation-hold", str(self.app.config.get("simulation_hold", 1)),
            "--canvas-width",
            "0",
            "--canvas-height",
            "0",
            "--anchor-canvas",
            "c",
            "--anchor-text",
            "c",
            "--terminal-background-color",
            background,
            "--no-eol",
            "--no-restore-cursor",
        ]
        if self.app.config.get("override_effect_colors", True) is True:
            argv.append("--no-color")
        return argv

    def _start(self) -> bool:
        if self.app.stopping or self.closing or self.running:
            return GLib.SOURCE_REMOVE
        self.running = True
        self.effect_started = None
        shared = (self.app.shared_effect_name() if self.app.config.get("shared_effect") and not self.windowed else None)
        # Preview uses the same effect-completion and hold lifecycle as the
        # screensaver, but keeps a separate, non-repeating selection cursor.
        playlist = (self.app.preview_sequence.current() if self.windowed else
                    self.app.current_playlist_effect if self.app.config.get("playlist_mode") else None)
        try:
            self.effect_label = select_effect(
                self.app.config, playlist_effect=playlist, shared_effect=shared,
                rotation=self._effect_bag,
            )
        except ValueError as error:
            print(f"ascii-saver: {error}", file=sys.stderr)
            self.running = False
            self.app.quit_saver()
            return GLib.SOURCE_REMOVE
        self.current_artwork_path = self._artwork_path()
        self._auto_fit_monitor_artwork()
        argv = effect_args(self._tte_argv(), self.effect_label)
        # The patched ttfx executable reports output frames after each run.
        # A unique per-run file avoids clashes between monitors.
        from tempfile import mkstemp
        fd, stats_name = mkstemp(prefix="ttfx-stats-", suffix=".json")
        os.close(fd)
        self.current_stats_path = Path(stats_name)
        argv[1:1] = ["--stats-file", stats_name]

        # A selected effect is not a launched effect. Defer logging until
        # VTE reports a successfully spawned child with a real PID.
        self.pending_effect_log = {
            "monitor": self.monitor_id,
            "effect": self.effect_label,
            "fps_cap": self.effective_fps_cap,
            "speed_multiplier": float(self.app.config.get("speed", 1.0)),
        }
        self.terminal.spawn_async(
            pty_flags=Vte.PtyFlags.DEFAULT,
            working_directory=str(Path.home()),
            argv=argv,
            envv=None,
            spawn_flags=GLib.SpawnFlags.SEARCH_PATH,
            child_setup=None,
            timeout=-1,
            cancellable=self.cancellable,
            callback=self._on_spawned,
            user_data=self,
        )
        return GLib.SOURCE_REMOVE

    def _discard_pending_frame_report(self) -> None:
        """Discard a report when no successful child completion will consume it."""
        path = getattr(self, "current_stats_path", None)
        self.current_stats_path = None
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError as error:
                print(f"ascii-saver: could not clean report {path}: {error}", file=sys.stderr)

    def _record_spawn_result(self, success: bool, message: str = "", pid=None) -> None:
        from spawn_events import spawn_event
        record = spawn_event(getattr(self, "pending_effect_log", None),
                             success, message=message, pid=pid, timestamp=time.time())
        self.pending_effect_log = None
        if record is None:
            return
        try:
            self.app.perf_log.append(record)
        except OSError as error:
            print(f"ascii-saver: logging error: {error}", file=sys.stderr)

    def _on_spawned(self, _terminal, pid, error, _data) -> None:
        if error is not None:
            self._discard_pending_frame_report()
            self._record_spawn_result(False, str(error.message))
            self.running = False
            if self.app.stopping or self.closing or self.cancellable.is_cancelled():
                return
            print(f"ascii-saver: could not start animation: {error.message}", file=sys.stderr)
            self.app.quit_saver()
        elif pid > 0:
            self._record_spawn_result(True, pid=pid)
            # Record only a successfully launched artwork, not an arbitrary
            # selection. A running monitor writes at most once per new asset.
            seen = getattr(self.app, '_recorded_artworks', None)
            if seen is None:
                self.app._recorded_artworks = set()
                seen = self.app._recorded_artworks
            key = (self.monitor_id, str(self.current_artwork_path))
            if key not in seen:
                seen.add(key)
                try:
                    from artwork_history import remember_artwork
                    remember_artwork(CONFIG_DIR, self.current_artwork_path)
                except (OSError, ValueError) as error:
                    print(f"ascii-saver: artwork history unavailable: {error}", file=sys.stderr)
            self.child_pid = pid
            self.effect_started = time.monotonic()
        elif pid == -1:
            self._discard_pending_frame_report()
            self._record_spawn_result(False, "VTE returned no child PID")
            self.running = False
            if not self.app.stopping and not self.closing:
                self.app.quit_saver()

    def _on_child_exited(self, _terminal, status) -> None:
        self.terminal.feed(b"\x1b[?25l")
        stats_path = getattr(self, "current_stats_path", None)
        self.current_stats_path = None
        if stats_path is not None:
            try:
                import json
                report = json.loads(stats_path.read_text(encoding="utf-8"))
                sample = parse_frame_report(report, expected_effect=self.effect_label)
                if sample is not None:
                    self.app.perf_log.append({
                        "event": "frame_stats", "wall_timestamp": time.time(),
                        "monitor": self.monitor_id, "effect": self.effect_label,
                        **sample,
                    })
                else:
                    print("ascii-saver: invalid or unsuccessful ttfx frame report", file=sys.stderr)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                print(f"ascii-saver: frame statistics unavailable: {exc}", file=sys.stderr)
            finally:
                # File cleanup is best-effort: an inaccessible temporary
                # report must never abort the VTE child-exited callback and
                # strand other displays at the synchronization barrier.
                try:
                    stats_path.unlink(missing_ok=True)
                except OSError as error:
                    print(f"ascii-saver: could not clean report {stats_path}: {error}",
                          file=sys.stderr)
        if self.effect_started is not None:
            now = time.monotonic()
            try:
                mon = getattr(self, "monitor", None)
                label = mon.get_connector() if mon and hasattr(mon, "get_connector") else "preview"
                self.app.perf_log.append({
                    "event": "effect_duration", "wall_timestamp": time.time(),
                    "monitor": label or "unknown", "effect": self.effect_label,
                    "duration_seconds": round(max(0, now-self.effect_started), 3),
                    "success": bool(tte_exit_ok(status)),
                })
            except (OSError, ValueError) as error:
                print(f"ascii-saver: logging error: {error}", file=sys.stderr)
            self.effect_started = None
        self.child_pid = None
        self.running = False
        if self.app.once:
            self.app.quit_saver()
            return
        if self.app.stopping or self.closing:
            return
        if tte_exit_ok(status):
            self.tte_failures = 0
            # The ttfx terminal *already contains its final rendered frame*,
            # including per-character ANSI colors and exact cell positions.
            # Redrawing logo.txt here cleared those colors and recentered it
            # differently, causing the reported horizontal jump at the hold.
            # Leave the VTE frame untouched until the next effect starts.
            if not self.windowed:
                # Per-monitor animations may be different. Finishing marks the
                # beginning of this monitor's independent final-artwork hold.
                self.app.monitor_effect_finished(self)
            else:
                # Only a successful effect advances the preview's palette.
                # Failed child launches/restarts retain the same color.
                self.palette_tick += 1
                # Windowed preview follows the *entire* sequence, not the
                # initial effect forever. The fullscreen barrier advances the
                # shared scheduler in _advance_when_all_ready; preview does not.
                self.app.preview_sequence.advance()
                hold_ms = int(1000 * float(self.app.config.get("effect_hold_seconds", 3)))
                GLib.timeout_add(max(1, hold_ms + TTE_SUCCESS_RESTART_MS), self._start)
            return
        self.tte_failures += 1
        delay = tte_failure_delay_ms(self.tte_failures)
        if delay is None:
            print(
                f"ascii-saver: animation exited with status {status}; "
                f"giving up after {TTE_MAX_FAILURES} failures",
                file=sys.stderr,
            )
            self.app.quit_saver()
            return
        print(
            f"ascii-saver: animation exited with status {status}; "
            f"retrying in {delay} ms ({self.tte_failures}/{TTE_MAX_FAILURES})",
            file=sys.stderr,
        )
        GLib.timeout_add(delay, self._start)


class SaverApplication(Gtk.Application):
    def __init__(self, *, windowed: bool, once: bool):
        # Same Wayland desktop identity as Dashboard and Preferences. NON_UNIQUE
        # keeps this rendering process separate from the registered GUI process.
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.windowed = windowed
        self.once = once
        self.config = load_config(CONFIG_DIR / "config.json")
        self.stopping = False
        self.pid_file: Path | None = None
        self._monitors = None
        self.shared_round = 0
        self._shared_effect_cache = None
        self._shared_effect_round = -1
        self._shared_effect_bag = EffectShuffleBag()
        self.shared_finished = set()
        self.shared_pending = set()
        self.perf_log = BoundedLog(Path(os.environ.get("XDG_CACHE_HOME", str(Path.home()/".cache"))) / "ascii-saver" / "performance.jsonl")
        self.perf_sampler = ProcessSampler(window_seconds=300)
        self.perf_recorder = JsonlRecorder(Path(os.environ.get("XDG_CACHE_HOME", str(Path.home()/".cache"))) / "ascii-saver" / "performance.jsonl")
        GLib.timeout_add_seconds(1, self._sample_performance)
        playlists = self.config.get("playlists") or DEFAULT_PLAYLISTS
        excluded = self.config.get("exclude_effects", [])
        # A preview must not consume the fullscreen playlist cursor. Each
        # session starts at its own first effect and advances independently.
        self.playlist_scheduler = Scheduler(playlists, excluded)
        self.preview_playlist_scheduler = Scheduler(playlists, excluded)
        self.current_playlist_effect = (self.playlist_scheduler.next()
                                        if self.config.get("playlist_mode") else None)
        self.preview_sequence = PreviewSequence(self.config, self.preview_playlist_scheduler)
        self._screen_lock_backend = select_screen_lock_backend()
        self._screen_lock_bus: Gio.DBusConnection | None = None
        self._screen_lock_subscriptions: list[int] = []
        self._screen_lock_ready = False
        self._screen_lock_query_pending = False
        self._cursor_lease: FullscreenCursorLease | None = None
        # Probed in do_startup after GTK connects a display; fullscreen fallback otherwise.
        self.layer_shell = False

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        if not self._watch_screen_lock():
            # This application is a visual overlay, never a locking surface.
            # Fail closed when lock handoff cannot be observed.
            print(
                f"ascii-saver: could not monitor {self._screen_lock_backend.name}; refusing to start",
                file=sys.stderr,
            )
            self.stopping = True
            self.quit()
            return
        self._cursor_lease = FullscreenCursorLease(
            Gio, self._screen_lock_bus,
            # V66 uses the GTK overlay by default. Keep V65's extension
            # lease only behind an explicit opt-in for troubleshooting.
            enabled=(not self.windowed and self._screen_lock_backend == GNOME
                     and os.environ.get("ASCII_SAVER_GNOME_CURSOR_BRIDGE") == "1"),
        )
        display = Gdk.Display.get_default()
        self.layer_shell = bool(
            display is not None and Gtk4LayerShell is not None and Gtk4LayerShell.is_supported()
        )
        css = Gtk.CssProvider()
        css.load_from_data(b"window, vte-terminal { background: #000; padding: 0; margin: 0; }")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        # Register the action before assigning its accelerator. Previously
        # "app.quit" did not exist, so Escape relied entirely on the window's
        # key controller. Keep windowed previews independent of that shortcut.
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._on_quit_action)
        self.add_action(quit_action)
        if not self.windowed:
            self.set_accels_for_action("app.quit", ["Escape"])

    def _on_quit_action(self, *_args) -> None:
        self.quit_saver()

    def do_activate(self) -> None:
        # The initial GetActive reply must arrive before any visual surface is
        # created. This avoids a brief overlay when a process is launched into
        # an already-locked session.
        if self.stopping or not self._screen_lock_ready:
            return
        if self.get_windows():
            for window in self.get_windows():
                window.present()
            return

        if self.pid_file is None:
            try:
                self.pid_file = write_pid_file(pid_file_path(), os.getpid())
            except (OSError, RuntimeError) as error:
                print(f"ascii-saver: {error}", file=sys.stderr)
                self.quit()
                return
        if self.windowed:
            SaverWindow(self, None, True)
            return

        display = Gdk.Display.get_default()
        self._monitors = display.get_monitors() if display else None
        if self._monitors is not None:
            self._monitors.connect("items-changed", self._on_monitors_changed)
        self._sync_monitor_windows()

    def _watch_screen_lock(self) -> bool:
        """Subscribe before creating windows, then query the current lock state."""
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error:
            return False
        if bus is None:
            return False

        self._screen_lock_bus = bus
        lock = self._screen_lock_backend
        self._screen_lock_subscriptions = []
        if lock.about_to_lock:
            self._screen_lock_subscriptions.append(bus.signal_subscribe(
                "org.kde.screensaver", "org.kde.screensaver", "AboutToLock",
                "/ScreenSaver", None, Gio.DBusSignalFlags.NONE,
                self._on_about_to_lock, None,
            ))
        self._screen_lock_subscriptions.append(bus.signal_subscribe(
            lock.destination, lock.interface, "ActiveChanged", lock.path,
            None, Gio.DBusSignalFlags.NONE, self._on_active_changed, None,
        ))
        # Keep the Gtk.Application registered while do_activate waits for this
        # asynchronous reply; otherwise it can exit because it has no window.
        self.hold()
        self._screen_lock_query_pending = True
        try:
            bus.call(
                lock.destination,
                lock.path,
                lock.interface,
                "GetActive",
                None,
                GLib.VariantType.new("(b)"),
                Gio.DBusCallFlags.NONE,
                1000,
                None,
                self._on_get_active_finished,
                None,
            )
        except GLib.Error:
            self._finish_screen_lock_query()
            return False
        return True

    def _finish_screen_lock_query(self) -> None:
        if self._screen_lock_query_pending:
            self._screen_lock_query_pending = False
            self.release()

    def _on_about_to_lock(self, *_args) -> None:
        self.quit_saver()

    def _on_active_changed(
        self,
        _connection,
        _sender_name,
        _object_path,
        _interface_name,
        _signal_name,
        parameters,
        _user_data,
    ) -> None:
        try:
            active = bool(parameters.unpack()[0])
        except (AttributeError, IndexError, TypeError):
            return
        if active:
            self.quit_saver()

    def _on_get_active_finished(self, connection, result, _user_data) -> None:
        try:
            active = bool(connection.call_finish(result).unpack()[0])
        except (GLib.Error, AttributeError, IndexError, TypeError) as error:
            if not self.stopping:
                print(
                    f"ascii-saver: could not query {self._screen_lock_backend.name}: {error}",
                    file=sys.stderr,
                )
                self.stopping = True
                self._finish_screen_lock_query()
                self.quit()
            return
        if self.stopping:
            self._finish_screen_lock_query()
            return
        if active:
            self._finish_screen_lock_query()
            self.quit_saver()
            return
        self._screen_lock_ready = True
        self.activate()
        self._finish_screen_lock_query()

    def _on_monitors_changed(self, _model, _position, _removed, _added) -> None:
        self._sync_monitor_windows()

    def _close_overlay_window(self, window: SaverWindow) -> None:
        window.closing = True
        window.cancellable.cancel()
        window.terminal.feed_child(bytes((3,)))
        window.destroy()

    def _sample_performance(self) -> bool:
        if self.stopping:
            return GLib.SOURCE_REMOVE
        # Shared GTK/VTE renderer cost belongs to the application as a whole,
        # not to any single monitor. Keep its process metrics separate.
        shared = self.perf_sampler.sample(os.getpid(), "__shared__", "GTK/VTE renderer")
        if shared:
            shared_record = shared.asdict()
            shared_record["event"] = "shared_process_sample"
            shared_record["wall_timestamp"] = time.time()
            try:
                self.perf_log.append(shared_record)
            except OSError as error:
                print(f"ascii-saver: shared logging error: {error}", file=sys.stderr)
        for index, window in enumerate(self._overlay_windows()):
            pid = getattr(window, "child_pid", None)
            if not pid:
                continue
            mon = getattr(window, "monitor", None)
            label = mon.get_connector() if mon and hasattr(mon, "get_connector") else f"display-{index + 1}"
            s = self.perf_sampler.sample(pid, label or f"display-{index+1}", window.effect_label)
            if s:
                record = s.asdict()
                record['wall_timestamp'] = time.time()
                try:
                    self.perf_log.append(record)
                except OSError as error:
                    print(f"ascii-saver: logging error: {error}", file=sys.stderr)
        return GLib.SOURCE_CONTINUE

    def shared_effect_name(self) -> str:
        """One randomly selected effect per synchronized round, no immediate repeat."""
        if self._shared_effect_round != self.shared_round:
            self._shared_effect_cache = self._shared_effect_bag.next(
                [name for name in EFFECTS if name not in self.config.get("exclude_effects", [])])
            self._shared_effect_round = self.shared_round
        return self._shared_effect_cache

    def monitor_effect_finished(self, window) -> None:
        """Record completion once, leaving the VTE final frame untouched."""
        if self.stopping or window.closing or window not in self._overlay_windows():
            return
        if window in self.shared_pending or window in self.shared_finished:
            return
        self.shared_pending.add(window)
        hold_ms = int(1000 * float(self.config.get("effect_hold_seconds", 3)))
        round_number = self.shared_round
        GLib.timeout_add(max(1, hold_ms), self._monitor_ready, window, round_number)

    def _monitor_ready(self, window, round_number) -> bool:
        if (self.stopping or window.closing or round_number != self.shared_round
                or window not in self._overlay_windows()
                or window not in self.shared_pending):
            return GLib.SOURCE_REMOVE
        self.shared_pending.discard(window)
        self.shared_finished.add(window)
        self._advance_when_all_ready()
        return GLib.SOURCE_REMOVE

    def _start_monitors_for_round(self, windows, round_number: int) -> bool:
        """Launch a monitor cohort in one GTK main-loop dispatch.

        A queued timer may outlive a monitor hotplug, an automatic advance, or
        a shutdown. It must never restart a window from an obsolete round.
        `SaverWindow._start` retains its own running/closing guard.
        """
        if self.stopping or round_number != self.shared_round:
            return GLib.SOURCE_REMOVE
        live = set(self._overlay_windows())
        for window in windows:
            if self.stopping or round_number != self.shared_round:
                break
            if window in live and not window.closing:
                window._start()
        return GLib.SOURCE_REMOVE

    def _advance_when_all_ready(self) -> None:
        if self.stopping:
            return
        windows = [w for w in self._overlay_windows() if not w.closing]
        if not windows or not all(w in self.shared_finished for w in windows):
            return
        self.shared_round += 1
        self.shared_pending.clear()
        if self.config.get("playlist_mode"):
            self.current_playlist_effect = self.playlist_scheduler.next()
        self.shared_finished.clear()
        # One main-loop timer for every monitor: the palette/playlist round
        # advances once, then the cohort receives its start requests together.
        GLib.timeout_add(TTE_SUCCESS_RESTART_MS, self._start_monitors_for_round,
                         tuple(windows), self.shared_round)

    def _announce_cursor_lease(self) -> None:
        """Let an explicitly installed GNOME Shell extension hide the cursor.

        Never activates for windowed preview, KDE, or a non-mapped overlay.
        The bus name is dropped on quit, GNOME lock, or an unexpected crash.
        """
        if self.stopping or self.windowed or self._cursor_lease is None:
            return
        if any(window.get_mapped() for window in self._overlay_windows() if not window.closing):
            self._cursor_lease.acquire()

    def _overlay_windows(self) -> list[SaverWindow]:
        return [window for window in self.get_windows() if not getattr(window, "windowed", False)]

    def _sync_monitor_windows(self) -> None:
        if self.stopping or self.windowed:
            return
        current = []
        if self._monitors is not None:
            current = [self._monitors.get_item(index) for index in range(self._monitors.get_n_items())]
        alive = set(current)
        for window in list(self._overlay_windows()):
            monitor = getattr(window, "monitor", None)
            if current:
                if monitor is None or monitor not in alive:
                    self._close_overlay_window(window)
            elif monitor is not None:
                self._close_overlay_window(window)
        self.shared_finished.intersection_update(self._overlay_windows())
        self.shared_pending.intersection_update(self._overlay_windows())
        remaining = {window.monitor for window in self._overlay_windows()}
        newly_added = []
        if current:
            primary = current[0]
            # A layer-shell surface needs keyboard interactivity when it is
            # first mapped. Do not map every initial monitor with NONE and
            # only request EXCLUSIVE after present(). This also makes the
            # keyboard owner deterministic on multi-display startup.
            if self.layer_shell:
                # If the primary monitor changed, demote any old owner before
                # mapping a newly primary surface.
                self._refresh_keyboard_surface()
            for monitor in current:
                if monitor not in remaining:
                    newly_added.append(SaverWindow(
                        self, monitor, False, keyboard_surface=(monitor is primary),
                        defer_start=True,
                    ))
            self._refresh_keyboard_surface()
            self._advance_when_all_ready()
        elif not self._overlay_windows():
            newly_added.append(SaverWindow(
                self, None, False, keyboard_surface=True, defer_start=True,
            ))
        if newly_added:
            # Batch a first launch (or newly hotplugged monitors) into one
            # callback. If the barrier advances meanwhile, its round timer
            # will start these windows instead and the old callback is inert.
            GLib.timeout_add(350, self._start_monitors_for_round,
                             tuple(newly_added), self.shared_round)

    def _refresh_keyboard_surface(self) -> None:
        if not self.layer_shell or Gtk4LayerShell is None:
            return
        primary = None
        if self._monitors is not None and self._monitors.get_n_items():
            primary = self._monitors.get_item(0)
        assigned = False
        for window in self._overlay_windows():
            exclusive = not assigned and (window.monitor is primary or primary is None)
            if exclusive:
                assigned = True
            Gtk4LayerShell.set_keyboard_mode(
                window,
                Gtk4LayerShell.KeyboardMode.EXCLUSIVE if exclusive else Gtk4LayerShell.KeyboardMode.NONE,
            )

    def quit_saver(self) -> None:
        if self.stopping:
            return
        self.stopping = True
        if self._cursor_lease is not None:
            self._cursor_lease.release()
        for window in list(self.get_windows()):
            if hasattr(window, "_discard_pending_frame_report"):
                window._discard_pending_frame_report()
            window.closing = True
            window.cancellable.cancel()
            window.terminal.feed_child(bytes((3,)))
            window.destroy()
        self.quit()

    def do_shutdown(self) -> None:
        if self._cursor_lease is not None:
            self._cursor_lease.release()
        bus = self._screen_lock_bus
        if bus is not None:
            for subscription in self._screen_lock_subscriptions:
                bus.signal_unsubscribe(subscription)
        self._screen_lock_subscriptions.clear()
        self._screen_lock_bus = None
        path = self.pid_file
        if path is not None:
            try:
                if path.read_text(encoding="ascii").strip() == str(os.getpid()):
                    path.unlink(missing_ok=True)
            except OSError:
                pass
        Gtk.Application.do_shutdown(self)


def main() -> int:
    parser = argparse.ArgumentParser(description="ASCII Saver terminal screensaver for GNOME and KDE Plasma")
    parser.add_argument("--version", action="version", version=f"ASCII Saver {VERSION}")
    parser.add_argument("--windowed", action="store_true", help="open one decorated preview window")
    parser.add_argument("--once", action="store_true", help="exit after one animation")
    args = parser.parse_args()
    if runtime_dir() is None:
        print("ascii-saver: XDG_RUNTIME_DIR is unset; refusing to start", file=sys.stderr)
        return 1
    Adw.init()
    app = SaverApplication(windowed=args.windowed, once=args.once)
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, lambda *_unused: GLib.idle_add(app.quit_saver))
    return app.run([sys.argv[0]])


if __name__ == "__main__":
    raise SystemExit(main())
