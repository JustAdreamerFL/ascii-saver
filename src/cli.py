#!/usr/bin/env python3
"""Single installed command dispatcher for ASCII Saver.

Keep CLI argument parsing independent of PyGObject so --help and --version
work even if desktop libraries, GTK, or the display server are unavailable.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from helpers import read_version

CONTROL_COMMANDS = (
    "start", "preview", "stop", "status", "doctor", "components",
    "edit", "config", "enable", "disable", "uninstall",
)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ascii-saver",
        description="ASCII Saver: terminal screensaver and control app for GNOME and KDE Plasma",
        epilog="Examples: ascii-saver | ascii-saver preferences | ascii-saver start | ascii-saver stop",
    )
    parser.add_argument("--version", action="version", version=f"ASCII Saver {read_version()}")
    # Preserve old invocation paths used by automation and existing scripts.
    parser.add_argument("--windowed", action="store_true", help="legacy: run windowed renderer in the foreground")
    parser.add_argument("--once", action="store_true", help="legacy: quit renderer after one animation")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    commands.add_parser("dashboard", help="open the main control window")
    commands.add_parser("gui", help="alias of dashboard")
    for name in ("preferences", "prefs", "settings"):
        commands.add_parser(name, help="open Preferences directly" if name == "preferences" else "alias of preferences")
    commands.add_parser("playlist", help="open the Playlist Editor")
    play = commands.add_parser("play", help="run renderer in foreground (for scripts/debugging)")
    play.add_argument("--windowed", action="store_true", help="one decorated renderer window")
    play.add_argument("--once", action="store_true", help="quit after one effect")
    for name in CONTROL_COMMANDS:
        commands.add_parser(name, help={
            "start": "start fullscreen screensaver", "preview": "start windowed preview",
            "stop": "stop running renderer", "status": "show renderer and watcher status",
            "doctor": "diagnose installation", "components": "show component versions",
            "edit": "edit the default artwork file", "config": "open the config file",
            "enable": "enable automatic activation", "disable": "disable automatic activation",
            "uninstall": "remove the installed application (preserves user data)",
        }.get(name, name))
    delay = commands.add_parser("delay", help="set idle activation delay")
    delay.add_argument("seconds", type=int)
    dock = commands.add_parser("dock", help="GNOME dock integration")
    dock.add_argument("action", nargs="?", choices=("status", "apply", "restore"), default="status")
    return parser


def target_for(args: argparse.Namespace) -> tuple[str, list[str]]:
    """Return target script and args; can be unit-tested without GTK."""
    command = args.command
    if command in ("dashboard", "gui"):
        if args.windowed or args.once:
            raise ValueError("--windowed/--once require 'play' or no command")
        return "settings.py", []
    if command is None and not (args.windowed or args.once):
        return "settings.py", []
    if command in ("preferences", "prefs", "settings"):
        if args.windowed or args.once:
            raise ValueError("renderer flags require the 'play' command")
        return "settings.py", ["--preferences"]
    if command == "playlist":
        return "settings.py", ["--playlist-editor"]
    if command == "play" or command is None:
        options = []
        if args.windowed:
            options.append("--windowed")
        if args.once:
            options.append("--once")
        return "app.py", options
    if args.windowed or args.once:
        raise ValueError("--windowed/--once can only be used with 'play' or without a command")
    if command == "delay":
        return "ctl.py", ["delay", str(args.seconds)]
    if command == "dock":
        return "ctl.py", ["dock", args.action]
    return "ctl.py", [command]


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        script, script_args = target_for(args)
    except ValueError as exc:
        parser.error(str(exc))
    path = Path(__file__).resolve().with_name(script)
    if not path.is_file():
        parser.exit(1, f"ascii-saver: installed component missing: {script}\n")
    os.execv(sys.executable, [sys.executable, str(path), *script_args])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
