"""Single source of renderer and idle-watcher UI status."""
import ctl
from helpers import load_config


def automatic_activation_label(enabled: bool, watcher_running: bool) -> str:
    """Don't confuse the watcher process with the automatic activation setting."""
    if not enabled:
        return "Paused · Start Now and Preview still work"
    if not watcher_running:
        return "Enabled · idle watcher not detected"
    return "Enabled · launches the screensaver after the idle delay"


def current_status():
    saver = ctl.current_pid()
    watcher = ctl.current_watcher_pid()
    cfg = load_config(ctl.config_file)
    enabled = bool(cfg.get("enabled"))
    preview = bool(saver and ctl.is_windowed_preview(saver))
    return {
        "renderer": ("Preview running" if preview else "Fullscreen running") if saver else "Stopped",
        "watcher": ("Monitoring" if enabled else "Running (automatic launch disabled)") if watcher else "Not running",
        "automatic": automatic_activation_label(enabled, bool(watcher)),
        "preview": preview,
        "saver_running": bool(saver),
    }
