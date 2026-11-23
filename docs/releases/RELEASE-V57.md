# V57: Native GNOME Idle Watcher (experimental)

## Why
V56's installer always configured the Qt6/KIdleTime watcher, so a GNOME-only
Fedora laptop failed at `find_package(Qt6)` even though GTK and libadwaita
were present. A Python GNOME watcher would avoid Qt but load a separate Python
runtime continuously. This release selects a native C + GLib/GIO watcher for
GNOME and preserves Qt/KIdleTime on KDE Plasma.

## Implementation
- GNOME watcher: `gnome_idle_watcher.c` (GIO D-Bus for Mutter IdleMonitor,
  GLib main loop, Json-GLib config handling, GSubprocess child management).
- Reads the same user configuration; honours idle delay, enabled state,
  GNOME SessionManager idle inhibitors, GNOME screen lock state.
- Starts the existing GTK/VTE screensaver on an idle D-Bus event and stops its
  own child when GNOME signals input activity.
- Uses a PID file in XDG_RUNTIME_DIR and exits cleanly on signals.
- Detects GNOME via XDG_CURRENT_DESKTOP; `KDE_ASCII_SAVER_BACKEND=gnome|kde`
  manually overrides selection.
- Builds GNOME watcher with `cc` and `pkg-config` (`gio-2.0`, `json-glib-1.0`),
  **without Qt or KDE build dependencies**. Fedora packages: `gcc`,
  `pkgconf-pkg-config`, `glib2-devel`, `json-glib-devel`.
- Systemd service uses the GNOME-specific unit under the existing managed
  service name; installation also supports XDG autostart fallback.
- Rust `ttfx` uses the persistent Cargo cache introduced earlier.

## Limitations
- The GNOME C watcher has not been compiled or exercised against a real
  Mutter desktop here; the environment lacks GIO/Json-GLib development
  headers and cannot obtain them. The installer branch is regression-tested
  with a mock compiler and package metadata.
- GNOME's native IdleMonitor availability and behavior depend on Mutter.
- GTK4 Layer Shell is optional; GNOME usually uses regular fullscreen
  windows instead of a privileged layer-shell surface.
- Fullscreen-game detection via the KDE-specific KWin script does not apply
  to GNOME; GNOME idle inhibitors and screen lock are respected.
- This is not KScreenLocker integration or a replacement GNOME lock screen.

## Verification
Run on GNOME before installation:

```sh
KDE_ASCII_SAVER_BACKEND=gnome ./install.sh --check
```

Then `./install.sh`, and inspect:

```sh
systemctl --user status kde-ascii-saver.service
journalctl --user -u kde-ascii-saver.service -n 60 --no-pager
```

To inspect the actual steady-state memory footprint, compare
`/proc/<watcher-pid>/smaps_rollup` before and after GNOME idle activation.
