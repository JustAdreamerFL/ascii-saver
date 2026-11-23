"""Collect the modular settings UI source for offline behavioral contracts."""
from _bootstrap import read_source
UI_MODULES = (
    "settings.py", "preferences_shell.py", "preferences_controls.py", "preferences_pages.py",
    "preferences_gallery.py", "preferences_gallery_view.py", "preferences_displays.py",
    "preferences_state.py", "preferences_actions.py",
)
def all_ui_source():
    return "\n".join(read_source(name) for name in UI_MODULES)
