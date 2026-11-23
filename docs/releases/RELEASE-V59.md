# ASCII Saver 0.59.0

- Renamed application identity, launcher commands, desktop entry, service, config and cache directories from `kde-ascii-saver` to `ascii-saver`.
- Added backward-compatible migration of old preferences, artwork and Cargo cache without deleting source configuration.
- Fixed GNOME startup: queries `org.gnome.ScreenSaver` for lock state, not the freedesktop idle-inhibition service. KScreenLocker remains the KDE backend.
- Updated diagnostics and added offline tests for the backend choice.
- Logged deferred GNOME Wayland fullscreen / layer-shell behavior check in `GNOME-VALIDATION.md`.

Not tested in a live GNOME or Plasma session here. GNOME lock state must be checked on the actual Fedora machine.

## Installation and upgrade

From the extracted `ascii-saver-v59` directory, run `./install.sh`.
Existing V58 settings are copied from `~/.config/kde-ascii-saver/` to
`~/.config/ascii-saver/` if the new configuration directory does not yet
exist. The original files are preserved as a rollback backup. Cargo build
artifacts and renderer performance records move from `~/.cache/kde-ascii-saver/`
to `~/.cache/ascii-saver/` when the destination does not exist.

Use `ascii-saverctl prefs` and `ascii-saverctl preview` after the update.
The old service is stopped and disabled during a normal upgrade. When using
`--no-start`, the previous service is intentionally preserved until a normal
upgrade, to avoid modifying a running service unexpectedly.
