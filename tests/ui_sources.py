"""Collect the modular settings UI source for offline behavioral contracts."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
UI_MODULES = (
    "settings.py", "preferences_shell.py", "preferences_controls.py", "preferences_pages.py",
    "preferences_gallery.py", "preferences_gallery_view.py", "preferences_displays.py",
    "preferences_state.py", "preferences_actions.py",
)
def all_ui_source():
    return "\n".join((ROOT / name).read_text(encoding="utf-8") for name in UI_MODULES)
