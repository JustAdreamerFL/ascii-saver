"""Inspectable build/runtime versions; no GTK and no service side effects.

The GUI build version is captured when Python imports build_info, not read
from the mutable installed VERSION file on every About dialog open. Running
watchers are matched by their /proc executable inode rather than trusting a
stale PID-file name or assuming systemd restarted after an upgrade.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from build_info import BUILD_VERSION


def _xdg(var: str, fallback: str) -> Path:
    return Path(os.environ.get(var, str(Path.home() / fallback))).expanduser()


def data_path() -> Path:
    return _xdg('XDG_DATA_HOME', '.local/share') / 'ascii-saver'


def watcher_backend(app_dir: Path) -> str:
    try:
        value = (app_dir / 'watcher-backend').read_text(encoding='utf-8').strip()
        return {'gnome': 'GNOME / Mutter', 'kde': 'KDE Plasma / KIdleTime'}.get(value, 'Unknown')
    except OSError:
        return 'Unknown (older installation)'


def _version_output(executable: Path) -> str | None:
    if not executable.is_file() or not os.access(executable, os.X_OK):
        return None
    try:
        result = subprocess.run([str(executable), '--version'], capture_output=True,
                                text=True, timeout=1.5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    line = result.stdout.strip().splitlines()
    return line[0].strip()[:120] if line else None


def _watcher_pid() -> int | None:
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not runtime:
        return None
    path = Path(runtime) / f'ascii-saver-watcher-{os.getuid()}.pid'
    try:
        pid = int(path.read_text().strip())
    except (OSError, ValueError):
        return None
    return pid if pid > 1 else None


def running_watcher_status(installed: Path, pid: int | None = None) -> str:
    """Safe, read-only comparison of executable identity; does not signal PIDs."""
    if pid is None:
        pid = _watcher_pid()
    if pid is None:
        return 'Not running (or PID file unavailable)'
    try:
        proc_exe = Path(f'/proc/{pid}/exe')
        path = os.readlink(proc_exe)
        # PID reuse / unexpected processes must never be reported as our daemon.
        if Path(path.removesuffix(' (deleted)')).name != 'ascii-saver-watcher':
            return 'Unable to verify running watcher'
        actual = proc_exe.stat()
        expected = installed.stat()
        if (actual.st_dev, actual.st_ino) == (expected.st_dev, expected.st_ino):
            return 'Up to date'
        return 'Restart required (older watcher is running)'
    except OSError:
        return 'Not running or unavailable'


def collect_versions(app_dir: Path | None = None) -> dict[str, str]:
    app_dir = data_path() if app_dir is None else app_dir
    try:
        package_version = (app_dir / 'VERSION').read_text().strip()
    except OSError:
        package_version = 'Not installed'
    watcher = app_dir / 'ascii-saver-watcher'
    engine = app_dir / 'venv/bin/ttfx'
    return {
        'ui': BUILD_VERSION,
        'installed': package_version,
        'ui_status': ('Current' if BUILD_VERSION == package_version else
                      'Restart the GUI to load the installed release' if package_version != 'Not installed' else
                      'Source checkout / not installed'),
        'renderer': _version_output(engine) or 'Not available',
        'watcher': _version_output(watcher) or 'Version unavailable',
        'backend': watcher_backend(app_dir),
        'running': running_watcher_status(watcher),
        'session': f"{os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')} / {os.environ.get('XDG_SESSION_TYPE', 'Unknown')}",
    }


def troubleshooting_report(versions: dict[str, str]) -> str:
    lines = ['ASCII Saver components']
    labels = {'ui': 'Running GUI', 'installed': 'Installed application', 'ui_status': 'GUI status',
              'renderer': 'Rust animation engine', 'watcher': 'Native idle watcher',
              'backend': 'Watcher integration', 'running': 'Watcher status',
              'session': 'Desktop session'}
    lines.extend(f'{labels[key]}: {value}' for key, value in versions.items())
    return '\n'.join(lines)
