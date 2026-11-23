# V58: Automatic desktop and compositor detection (experimental)

The V57 GNOME installer supported manual backend selection but still assumed
KDE for every non-GNOME session. V58 identifies the current DE and common
window managers/compositors, choosing the matching native idle watcher only
when it actually exists.

**Use without any override:**

```sh
./install.sh --detect-session  # show desktop, compositor/WM, selected backend
./install.sh --check           # check dependencies for detected backend
./install.sh                   # compile and install with detected backend
```

Detection follows freedesktop `XDG_CURRENT_DESKTOP`, then
`XDG_SESSION_DESKTOP` and `DESKTOP_SESSION`, then a cautious per-user process
fallback. KDE Plasma/KWin chooses Qt6/KIdleTime. GNOME/Mutter chooses C/GIO
and does not request Qt/KF6 packages. Unrecognized, Sway, Hyprland, niri,
COSMIC and other currently unsupported sessions are reported and not silently
assigned the KDE watcher. The graphical GTK application may run on those
desktops, but the automatic idle watcher has no implemented backend for them.

`KDE_ASCII_SAVER_BACKEND=gnome|kde` remains an optional troubleshooting
escape hatch and is not required for normal installation.

The compositor is inferred from session metadata unless a process fallback
was required. If desktop environment variables are missing or stale, the
command may not know which of multiple graphical sessions is active.

## Verification

- Automated detection tests for GNOME, KDE, XDG fallback and unsupported WMs.
- Existing installer tests exercise GNOME selection with no explicit backend.
- Python and shell tests run without compiling GTK, the GNOME watcher or Rust.
- Live desktop behavior still requires testing on GNOME and Plasma.
