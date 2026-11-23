#!/usr/bin/env python3
"""Control utility for ASCII Saver."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from screen_lock_backend import select_screen_lock_backend
from component_versions import collect_versions, troubleshooting_report
from gnome_dock import discover as discover_dock, report as dock_report, apply as dock_apply, restore as dock_restore
from helpers import (
    DEFAULT_CONFIG,
    editor_argv,
    load_config as load_config_file,
    new_config,
    pid_from_file,
    process_matches_saver,
    process_matches_watcher,
    read_version,
    runtime_dir,
    send_signal_if_matches,
)


home = Path.home()
config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
config_dir = config_home / "ascii-saver"
config_file = config_dir / "config.json"
package_dir = os.environ.get("ASCII_SAVER_PACKAGE_DIR")
data_dir = Path(package_dir).expanduser() if package_dir else data_home / "ascii-saver"
watcher_binary = Path(
    os.environ.get("ASCII_SAVER_WATCHER_BINARY", data_dir / "ascii-saver-watcher")
)
ttfx_binary = Path(os.environ.get("ASCII_SAVER_TTFX", data_dir / "venv" / "bin" / "ttfx"))
python_binary = Path(
    os.environ.get("ASCII_SAVER_PYTHON", data_dir / "venv" / "bin" / "python")
)
launcher = Path(
    os.environ.get("ASCII_SAVER_LAUNCHER", home / ".local" / "bin" / "ascii-saver")
)
settings_launcher = Path(
    os.environ.get(
        "ASCII_SAVER_SETTINGS_LAUNCHER", home / ".local" / "bin" / "ascii-saver-settings"
    )
)
service = "ascii-saver.service"
autostart_file = Path(
    os.environ.get(
        "ASCII_SAVER_AUTOSTART_FILE",
        config_home / "autostart" / "com.github.justadreamerfl.asciisaver.Watcher.desktop",
    )
)
VERSION = read_version()
LAUNCH_TIMEOUT_SECONDS = 3.0
STOP_TIMEOUT_SECONDS = 2.5
STOP_POLL_SECONDS = 0.05


def process_matches_installed_saver(pid: int) -> bool:
    return process_matches_saver(pid, data_dir / "app.py")


def process_matches_installed_watcher(pid: int) -> bool:
    return process_matches_watcher(pid, watcher_binary)


def pid_file() -> Path | None:
    directory = runtime_dir()
    return None if directory is None else directory / f"ascii-saver-{os.getuid()}.pid"


def watcher_pid_file() -> Path | None:
    directory = runtime_dir()
    return None if directory is None else directory / f"ascii-saver-watcher-{os.getuid()}.pid"


def systemd_user_available() -> bool:
    executable = shutil.which("systemctl")
    if executable is None:
        return False
    return subprocess.run(
        [executable, "--user", "show-environment"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def load_config() -> dict:
    return load_config_file(config_file)


def save_config(config: dict) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".config.json.", suffix=".tmp", dir=config_dir
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(config_file)
    finally:
        temporary.unlink(missing_ok=True)


def update_config_values(updates: dict) -> None:
    """Merge settings into config.json without clobbering an unreadable file."""
    if config_file.exists():
        try:
            loaded = json.loads(config_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SystemExit(
                f"ascii-saverctl: config.json is unreadable ({exc}); refusing to overwrite it"
            ) from exc
        if not isinstance(loaded, dict):
            raise SystemExit(
                "ascii-saverctl: config.json is not a JSON object; refusing to overwrite it"
            )
    else:
        loaded = {}
    config = new_config()
    config.update(loaded)
    config.update(updates)
    save_config(config)


def update_config(key: str, value) -> None:
    update_config_values({key: value})


def current_pid() -> int | None:
    path = pid_file()
    return None if path is None else pid_from_file(path, process_matches_installed_saver)


def is_windowed_preview(pid: int | None = None) -> bool:
    """Only the validated running saver can be treated as a preview.

    Proc cmdline is used to distinguish --windowed from fullscreen without
    relying on window titles or a second control PID file.
    """
    if pid is None:
        pid = current_pid()
    if not pid or not process_matches_installed_saver(pid):
        return False
    try:
        return b"--windowed" in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\x00")
    except OSError:
        return False


def current_watcher_pid() -> int | None:
    path = watcher_pid_file()
    return None if path is None else pid_from_file(path, process_matches_installed_watcher)


def command_start(windowed: bool = False) -> bool:
    active_pid = current_pid()
    if active_pid:
        preview_active = is_windowed_preview(active_pid)
        if preview_active != windowed:
            existing = "preview" if preview_active else "fullscreen screensaver"
            requested = "preview" if windowed else "fullscreen screensaver"
            print(
                f"Cannot start {requested}: the {existing} is already running. "
                "Stop it first; the active session was left untouched."
            )
            return False
        print("ASCII Saver preview is already open" if windowed
              else "ASCII Saver fullscreen screensaver is already running")
        return True
    # The public launcher opens the dashboard by default as of V105.
    # Explicit play keeps watcher/status PID semantics unchanged.
    args = [str(launcher), "play"]
    if windowed:
        args.append("--windowed")
    # Keep diagnostics from the entire renderer lifetime, not just the first
    # three seconds. A failure after an effect starts otherwise vanishes with
    # the temporary file while the user only sees the window disappear.
    log_dir = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache")) / "ascii-saver"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        # The previous session is kept for post-mortem debugging.
        log_path = log_dir / "renderer.log"
        previous = log_dir / "renderer.previous.log"
        if log_path.exists():
            log_path.replace(previous)
        fd = os.open(log_path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    except OSError as error:
        print(f"Could not open renderer diagnostic log: {error}")
        return False
    with os.fdopen(fd, "w+b") as diagnostics:
        try:
            process = subprocess.Popen(
                args,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=diagnostics,
            )
        except OSError as error:
            print(f"Could not start ASCII Saver: {error}")
            return False

        deadline = time.monotonic() + LAUNCH_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if current_pid():
                print("Started ASCII Saver preview" if windowed else "Started ASCII Saver")
                return True
            returncode = process.poll()
            if returncode is not None:
                diagnostics.seek(0)
                detail = diagnostics.read().decode("utf-8", errors="replace").strip()
                message = f"ASCII Saver exited during startup (status {returncode})"
                print(f"{message}: {detail}" if detail else message)
                return False
            time.sleep(0.05)

    try:
        process.terminate()
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=1)
        except (OSError, subprocess.TimeoutExpired):
            pass
    except OSError:
        pass
    print(
        "ASCII Saver did not finish initializing within "
        f"{LAUNCH_TIMEOUT_SECONDS:g} seconds and was stopped"
    )
    return False


def wait_for_renderer_exit(pid: int, timeout: float = STOP_TIMEOUT_SECONDS) -> bool:
    """Verify the identified renderer exited; never signal an unrelated process.

    The watcher may own the renderer, so there is no Popen object to wait on.
    Verify its original PID against our installed app path rather than merely
    waiting for a potentially stale PID file to disappear. Never force-kill.
    """
    deadline = time.monotonic() + timeout
    while process_matches_installed_saver(pid):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(STOP_POLL_SECONDS, remaining))
    return True


def command_stop() -> bool:
    pid = current_pid()
    if not pid:
        print("ASCII Saver is not running")
        return True
    try:
        signaled = send_signal_if_matches(pid, signal.SIGTERM, process_matches_installed_saver)
    except PermissionError:
        print("Could not stop ASCII Saver: permission denied")
        return False
    if not signaled:
        print("ASCII Saver is no longer running")
        return True
    if not wait_for_renderer_exit(pid):
        print("ASCII Saver is still shutting down. No force-kill was sent; "
              "check `ascii-saverctl status` or the renderer log.")
        return False
    print("Stopped ASCII Saver")
    return True


def command_edit() -> bool:
    logo = config_dir / "logo.txt"
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if editor:
        argv = editor_argv(editor)
        if argv:
            subprocess.run([*argv, str(logo)], check=False)
            return True
    return open_path(logo)


def open_path(path: Path) -> bool:
    try:
        subprocess.Popen(
            ["xdg-open", str(path)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as error:
        print(f"Could not open {path}: {error}")
        return False
    return True


def integration_status() -> str:
    if systemd_user_available():
        state = subprocess.run(
            ["systemctl", "--user", "is-active", service],
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
        return f"systemd user service ({state or 'unavailable'})"
    if current_watcher_pid() is not None:
        return "XDG session autostart (active)"
    if autostart_file.exists():
        return "XDG session autostart (starts next login)"
    return "unavailable"


def command_status() -> None:
    config = load_config()
    integration = integration_status()
    pid = current_pid()
    state = ("preview" if is_windowed_preview(pid) else "fullscreen") if pid else "stopped"
    print(f"running: {'yes' if pid else 'no'}")
    print(f"playback mode: {state}")
    print(f"automatic: {'enabled' if config.get('enabled', True) else 'disabled'}")
    print(f"idle delay: {config.get('idle_delay', 120)} seconds")
    print(f"Idle integration: {integration or 'unavailable'}")
    print(f"logo: {config_dir / 'logo.txt'}")


def command_settings() -> bool:
    try:
        subprocess.Popen(
            [str(settings_launcher)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as error:
        print(f"Could not open ASCII Saver settings: {error}")
        return False
    return True


def collect_diagnostics() -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    required_files = (
        data_dir / "app.py",
        data_dir / "settings.py",
        data_dir / "helpers.py",
        watcher_binary,
    )
    missing = [path.name for path in required_files if not path.is_file()]
    checks.append(
        (
            "application files",
            not missing,
            "installed" if not missing else f"missing: {', '.join(missing)}",
        )
    )

    python = python_binary if python_binary.is_file() else Path(shutil.which("python3") or "python3")
    namespace_check = """
import gi
for namespace, version in (("Gtk", "4.0"), ("Vte", "3.91")):
    gi.require_version(namespace, version)
from gi.repository import Gtk, Vte
"""
    if python.is_file() and os.access(python, os.X_OK):
        completed = subprocess.run(
            [str(python), "-c", namespace_check],
            text=True,
            capture_output=True,
            check=False,
        )
        detail = completed.stderr.strip().splitlines()
        checks.append(
            (
                "GTK 4 and VTE",
                completed.returncode == 0,
                "available"
                if completed.returncode == 0
                else (detail[-1] if detail else "unavailable"),
            )
        )
    else:
        checks.append(("GTK 4 and VTE", False, "application Python environment is missing"))

    tte = ttfx_binary
    if tte.is_file() and os.access(tte, os.X_OK):
        completed = subprocess.run(
            [str(tte), "--version"], text=True, capture_output=True, check=False
        )
        version = (completed.stdout or completed.stderr).strip().splitlines()
        checks.append(
            (
                "Rust ttfx",
                completed.returncode == 0,
                version[-1] if version else "installed",
            )
        )
    else:
        checks.append(("Rust ttfx", False, "ttfx binary is missing"))

    try:
        raw_config = json.loads(config_file.read_text(encoding="utf-8"))
        config_ok = isinstance(raw_config, dict)
        config_detail = "valid JSON object" if config_ok else "top-level value is not an object"
    except (OSError, ValueError) as error:
        config_ok = False
        config_detail = str(error)
    checks.append(("configuration", config_ok, config_detail))

    lock = select_screen_lock_backend()
    gdbus = shutil.which("gdbus")
    if gdbus is None:
        checks.append((f"{lock.name} D-Bus", False, "gdbus command is unavailable"))
    else:
        try:
            completed = subprocess.run(
                [
                    gdbus,
                    "call",
                    "--session",
                    "--dest",
                    lock.destination,
                    "--object-path",
                    lock.path,
                    "--method",
                    f"{lock.interface}.GetActive",
                ],
                text=True,
                capture_output=True,
                check=False,
                timeout=3,
            )
            detail = (completed.stdout or completed.stderr).strip().splitlines()
            checks.append(
                (
                    f"{lock.name} D-Bus",
                    completed.returncode == 0,
                    detail[-1] if detail else "no response",
                )
            )
        except subprocess.TimeoutExpired:
            checks.append((f"{lock.name} D-Bus", False, "query timed out"))
        except OSError as error:
            checks.append((f"{lock.name} D-Bus", False, str(error)))

    watcher = current_watcher_pid()
    integration = integration_status()
    integration_ok = watcher is not None or integration == "systemd user service (active)"
    checks.append(("idle watcher", integration_ok, integration))
    return checks


def command_doctor() -> bool:
    checks = collect_diagnostics()
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    passed = all(ok for _name, ok, _detail in checks)
    print("All checks passed." if passed else "One or more checks failed.")
    return passed


def command_uninstall() -> None:
    if package_dir:
        raise SystemExit(
            "ascii-saverctl: this is a system package installation; "
            "remove it with your distribution package manager"
        )
    installed_uninstaller = data_dir / "uninstall.sh"
    if not installed_uninstaller.is_file() or not os.access(installed_uninstaller, os.X_OK):
        raise SystemExit(
            "ascii-saverctl: the hardened uninstaller is missing; "
            "reinstall ASCII Saver or run uninstall.sh from a trusted source checkout"
        )
    completed = subprocess.run(
        [str(installed_uninstaller), "--non-interactive"],
        check=False,
    )
    if completed.returncode:
        raise SystemExit(
            f"ascii-saverctl: uninstaller exited with status {completed.returncode}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Control ASCII Saver")
    parser.add_argument("--version", action="version", version=f"ASCII Saver {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("start")
    sub.add_parser("preview")
    sub.add_parser("stop")
    sub.add_parser("edit")
    sub.add_parser("prefs")
    sub.add_parser("config")
    sub.add_parser("enable")
    sub.add_parser("disable")
    delay_parser = sub.add_parser("delay")
    delay_parser.add_argument("seconds", type=int)
    sub.add_parser("status")
    sub.add_parser("doctor")
    sub.add_parser("components")
    dock = sub.add_parser("dock", help="Check or explicitly configure GNOME Dash to Dock fullscreen behavior")
    dock.add_argument("action", choices=("status", "apply", "restore"), nargs="?", default="status")
    sub.add_parser("uninstall")
    args = parser.parse_args()

    if args.command == "start":
        return 0 if command_start() else 1
    elif args.command == "preview":
        return 0 if command_start(windowed=True) else 1
    elif args.command == "stop":
        return 0 if command_stop() else 1
    elif args.command == "edit":
        return 0 if command_edit() else 1
    elif args.command == "prefs":
        return 0 if command_settings() else 1
    elif args.command == "config":
        return 0 if open_path(config_file) else 1
    elif args.command in ("enable", "disable"):
        update_config("enabled", args.command == "enable")
        print(f"Automatic screensaver {args.command}d")
    elif args.command == "delay":
        if not 10 <= args.seconds <= 86400:
            parser.error("delay must be between 10 and 86400 seconds")
        update_config("idle_delay", args.seconds)
        print(f"Idle delay set to {args.seconds} seconds")
    elif args.command == "status":
        command_status()
    elif args.command == "doctor":
        return 0 if command_doctor() else 1
    elif args.command == "components":
        print(troubleshooting_report(collect_versions()))
    elif args.command == "dock":
        if args.action == "status":
            print(dock_report())
        else:
            settings = discover_dock()
            if settings is None:
                print("Dash to Dock schema unavailable. No settings changed.")
                return 1
            try:
                if args.action == "apply":
                    print(dock_apply(settings))
                else:
                    print(dock_restore(settings))
            except (OSError, RuntimeError, ValueError) as error:
                print(f"Could not manage dock preferences: {error}")
                return 1
    elif args.command == "uninstall":
        command_uninstall()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
