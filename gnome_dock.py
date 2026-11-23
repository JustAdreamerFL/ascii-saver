"""Opt-in, reversible GNOME Dash to Dock fullscreen compatibility settings.

GNOME Shell is the compositor and cannot be covered by an ordinary Wayland
client. This module changes only user-owned Dash to Dock preferences when the
user explicitly requests it. It never disables an extension, injects Shell JS,
or changes a lock screen.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

SCHEMA = "org.gnome.shell.extensions.dash-to-dock"
DOCK_UUIDS = ("dash-to-dock@micxgx.gmail.com", "ubuntu-dock@ubuntu.com")
# Values are GVariant literals accepted by gsettings set. All keys are part
# of the upstream Dash to Dock schema, but not every derivative exposes all.
FULLSCREEN_PROFILE = {
    "dock-fixed": "false",
    "autohide": "true",
    "intellihide": "true",
    "intellihide-mode": "'ALL_WINDOWS'",
    "autohide-in-fullscreen": "false",
}


def backup_file() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "ascii-saver" / "gnome-dock-backup.json"


def _execute(argv: list[str]) -> str:
    result = subprocess.run(argv, text=True, capture_output=True, check=False, timeout=5)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or f"Failed: {argv[0]}")
    return result.stdout.strip()


class DockSettings:
    def __init__(self, execute: Callable[[list[str]], str] = _execute,
                 schema_dir: str | None = None):
        self.execute = execute
        self.schema_dir = schema_dir

    def args(self, *rest: str) -> list[str]:
        prefix = ["gsettings"]
        if self.schema_dir:
            prefix.extend(("--schemadir", self.schema_dir))
        return [*prefix, *rest]

    def keys(self) -> set[str]:
        return set(self.execute(self.args("list-keys", SCHEMA)).splitlines())

    def get(self, key: str) -> str:
        return self.execute(self.args("get", SCHEMA, key))

    def set(self, key: str, value: str) -> None:
        self.execute(self.args("set", SCHEMA, key, value))


def discover(execute: Callable[[list[str]], str] = _execute) -> DockSettings | None:
    """Find a system or user-local extension schema without changing settings."""
    candidates: list[str | None] = [None]
    for root in (Path.home() / ".local/share/gnome-shell/extensions",
                 Path("/usr/share/gnome-shell/extensions")):
        for uuid in DOCK_UUIDS:
            directory = root / uuid / "schemas"
            if directory.is_dir():
                candidates.append(str(directory))
    for schema_dir in candidates:
        settings = DockSettings(execute, schema_dir)
        try:
            if SCHEMA in settings.execute(settings.args("list-schemas")).splitlines():
                return settings
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            continue
    return None


def _write_backup(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, tmpname = tempfile.mkstemp(prefix=".gnome-dock-", dir=path.parent)
    temporary = Path(tmpname)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump(data, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def inspect(settings: DockSettings | None) -> tuple[str, dict[str, tuple[str, str]]]:
    if settings is None:
        return "Dash to Dock settings schema not found", {}
    available = settings.keys()
    values = {key: (settings.get(key), wanted)
              for key, wanted in FULLSCREEN_PROFILE.items() if key in available}
    if not values:
        return "The installed dock exposes none of the supported settings", {}
    return ("Fullscreen profile already matches" if all(a == b for a, b in values.values())
            else "Fullscreen profile differs"), values


def apply(settings: DockSettings, path: Path | None = None) -> str:
    path = path or backup_file()
    if path.exists():
        return (f"A backup already exists at {path}. "
                "Use 'dock restore' before applying the profile again.")
    _message, values = inspect(settings)
    changes = {key: (old, new) for key, (old, new) in values.items() if old != new}
    if not changes:
        return "Dock settings already match the fullscreen profile; nothing changed."
    # Write the backup before the first change so interrupted runs are
    # recoverable. The restore command only resets values still equal to ours.
    _write_backup(path, {"format": 1, "schema": SCHEMA,
                         "schema_dir": settings.schema_dir,
                         "changes": {key: {"before": old, "applied": new}
                                     for key, (old, new) in changes.items()}})
    try:
        for key, (_old, new) in changes.items():
            settings.set(key, new)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        return (f"Unable to finish applying the profile: {error}. "
                f"The backup remains at {path}; run 'dock restore'.")
    return ("Fullscreen dock compatibility profile applied. "
            f"Original settings saved in {path}. "
            "This affects Dash to Dock globally until restored.")


def restore(settings: DockSettings, path: Path | None = None) -> str:
    path = path or backup_file()
    if not path.is_file():
        return "No ASCII Saver dock-settings backup to restore."
    try:
        backup = json.loads(path.read_text(encoding="utf-8"))
        if backup.get("schema") != SCHEMA or backup.get("format") != 1:
            raise ValueError("unknown backup format")
        changes = backup["changes"]
        if not isinstance(changes, dict):
            raise ValueError("invalid changes")
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise RuntimeError(f"Invalid dock backup at {path}: {error}") from error
    # Preserve user changes made since 'apply': only restore values that still
    # match what ASCII Saver applied, never overwrite a later manual choice.
    left = {}
    restored = 0
    for key, record in changes.items():
        if key not in FULLSCREEN_PROFILE or not isinstance(record, dict):
            left[key] = record
            continue
        before, applied = record.get("before"), record.get("applied")
        if not isinstance(before, str) or applied != FULLSCREEN_PROFILE[key]:
            left[key] = record
            continue
        try:
            current = settings.get(key)
            if current == applied:
                settings.set(key, before)
                restored += 1
            elif current != before:
                # User changed it; don't override and leave visible note.
                left[key] = record
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            left[key] = record
    if left:
        backup["changes"] = left
        _write_backup(path, backup)
        return (f"Restored {restored} setting(s); {len(left)} setting(s) left "
                "untouched due to user changes or errors. See backup: " + str(path))
    path.unlink()
    return f"Restored {restored} original dock setting(s)."


def report() -> str:
    settings = discover()
    message, values = inspect(settings)
    lines = [message]
    if settings:
        lines.append(f"Schema: {SCHEMA} ({settings.schema_dir or 'system'})")
        for key, (current, recommended) in values.items():
            lines.append(f"  {key}: {current} (fullscreen profile: {recommended})")
    path = backup_file()
    if path.exists():
        lines.append(f"Restore backup: {path}")
    lines.append("GNOME Shell may still show extension overlays after lock/unlock; "
                 "a Wayland app cannot override GNOME Shell stacking.")
    return "\n".join(lines)
