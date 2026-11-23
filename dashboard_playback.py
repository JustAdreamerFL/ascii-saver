"""Dashboard playback command execution without a GTK dependency."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable


def run_dashboard_command(
    requested: str,
    interpreter: str,
    cli: Path,
    preview_active: Callable[[], bool],
    runner=None,
) -> str:
    """Return an honest toast message for a verified CLI action.

    The CLI is the authority for mode conflicts and for verified shutdown.
    Never turn a nonzero exit into a success message.
    """
    if requested not in ("start", "preview-toggle"):
        raise ValueError("unexpected dashboard playback action")
    command = ("stop" if preview_active() else "preview") if requested == "preview-toggle" else "start"
    execute = subprocess.run if runner is None else runner
    try:
        completed = execute([interpreter, str(cli), command],
                            text=True, capture_output=True, check=False, timeout=10)
    except subprocess.TimeoutExpired:
        return f"{command} timed out; check the current status before retrying"
    except OSError as error:
        return f"{command} failed: {error}"
    if completed.returncode:
        return (completed.stderr or completed.stdout).strip() or f"{command} failed"
    return {"start": "Screensaver started", "preview": "Preview opened",
            "stop": "Preview closed"}[command]
