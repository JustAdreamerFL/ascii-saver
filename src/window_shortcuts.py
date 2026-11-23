"""GNOME-style window closing shortcuts. Close-request remains the authority.

Keeps unsaved-change confirmation intact in ArtworkEditor/Playlist Editor.
"""
from __future__ import annotations

def is_close_shortcut(name: str, ctrl: bool) -> bool:
    return name.lower() == 'escape' or (ctrl and name.lower() in ('w', 'q'))

def install_close_shortcuts(window, Gtk, Gdk):
    controller = Gtk.EventControllerKey()
    controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    def on_key(_controller, keyval, _keycode, state):
        key = Gdk.keyval_name(keyval) or ''
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        if is_close_shortcut(key, ctrl):
            window.close()  # honours close-request veto for unsaved edits
            return True
        return False
    controller.connect('key-pressed', on_key)
    window.add_controller(controller)
    return controller
