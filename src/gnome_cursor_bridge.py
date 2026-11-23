"""Optional fullscreen-only GNOME Shell pointer-visibility lease.

GNOME/Mutter owns the cursor when GNOME Shell actors such as docks are above a
normal Wayland client. GTK's per-surface invisible cursor is insufficient in
that case. An *opt-in* GNOME Shell extension watches this session D-Bus name,
and restores normal cursor visibility when its owner disappears.

No cursor visibility change is made by this module on its own. No GTK import is
needed, which makes the acquire/release lifecycle independently testable.
"""

from __future__ import annotations

import logging

FULLSCREEN_BUS_NAME = "com.github.justadreamerfl.asciisaver.Fullscreen"


class FullscreenCursorLease:
    def __init__(self, gio, connection, enabled: bool):
        self.gio = gio
        self.connection = connection
        self.enabled = enabled
        self.owner_id: int | None = None

    def acquire(self) -> bool:
        """Advertise a mapped fullscreen saver, never a windowed preview."""
        if not self.enabled or self.connection is None:
            return False
        if self.owner_id is not None:
            return True
        try:
            owner = self.gio.bus_own_name_on_connection(
                self.connection,
                FULLSCREEN_BUS_NAME,
                self.gio.BusNameOwnerFlags.NONE,
                None,
                None,
            )
            if not owner:
                return False
            self.owner_id = owner
            return True
        except Exception as error:
            logging.warning("GNOME cursor bridge unavailable: %s", error)
            return False

    def release(self) -> None:
        """Always give the cursor back on quit, lock, or application shutdown."""
        if self.owner_id is not None:
            owner = self.owner_id
            self.owner_id = None
            try:
                self.gio.bus_unown_name(owner)
            except Exception as error:
                logging.warning("Unable to release GNOME cursor lease: %s", error)
