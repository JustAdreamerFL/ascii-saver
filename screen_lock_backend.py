"""Select the real screen-lock D-Bus API for the active desktop.

The freedesktop *idle-inhibit* service on GNOME is not a screen-lock
service. Calling GetActive on it fails with NotSupported. Only the
GNOME Shell and KScreenLocker endpoints are valid here. Fail closed if
the appropriate service does not answer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Mapping


@dataclass(frozen=True)
class ScreenLockBackend:
    name: str
    destination: str
    path: str
    interface: str
    about_to_lock: bool = False


GNOME = ScreenLockBackend('GNOME Shell', 'org.gnome.ScreenSaver',
                          '/org/gnome/ScreenSaver', 'org.gnome.ScreenSaver')
KDE = ScreenLockBackend('KScreenLocker', 'org.freedesktop.ScreenSaver',
                        '/ScreenSaver', 'org.freedesktop.ScreenSaver', True)


def select_screen_lock_backend(env: Mapping[str, str] | None = None) -> ScreenLockBackend:
    env = os.environ if env is None else env
    backend = env.get('ASCII_SAVER_BACKEND', '').lower()
    if backend == 'gnome':
        return GNOME
    if backend == 'kde':
        return KDE
    session = ':'.join((env.get('XDG_CURRENT_DESKTOP', ''),
                        env.get('XDG_SESSION_DESKTOP', ''),
                        env.get('DESKTOP_SESSION', ''))).lower().replace(';', ':')
    tokens = [part.strip() for part in session.split(':') if part.strip()]
    # Prefer the primary reported desktop, but not generic substring matches:
    # GNOME and Plasma can both occur in unrelated file paths or session text.
    for token in tokens:
        if token in ('gnome', 'gnome-classic', 'ubuntu', 'ubuntu-wayland',
                     'ubuntu-xorg', 'gnome-wayland', 'gnome-xorg'):
            return GNOME
        if token in ('kde', 'plasma', 'plasmawayland', 'plasmax11', 'kde-plasma'):
            return KDE
    # Conservatively preserve the legacy KDE behavior if no desktop is known.
    # The installer itself rejects unsupported compositors.
    return KDE
