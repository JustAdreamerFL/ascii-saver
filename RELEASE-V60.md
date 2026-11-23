# ASCII Saver 0.60.0

## Fixes

- **Edit Artwork (Preferences / General):** open the existing in-app `Adw.Window` text editor directly, instead of running `ctl.py edit` in a subprocess with captured stdout. Captured terminal editors could output ANSI escape codes into the page rather than displaying a graphical editor.
- **Clean application identity:** installer and uninstaller operate only on `ascii-saver`. The installer does not copy, move, stop or remove the legacy `kde-ascii-saver` files, configuration, service or cache. This also means updating from an old KDE-prefixed release will **not** automatically import its settings.
- **User data safety:** existing `~/.config/ascii-saver/` artwork and preferences remain untouched on upgrades; the old installation can be uninstalled independently.

## KDE ASCII Saver V55 uninstall warning

Its `uninstall.sh` removes the application, launchers and service but deliberately **preserves** `~/.config/kde-ascii-saver` and does **not remove** `~/.cache/kde-ascii-saver`. If you want to clear the cache, remove that specific directory manually *after* uninstalling the old version. Delete the configuration only if you no longer need the settings and artwork.

## Verification

Source and installer tests can be run with `python3 -m unittest discover -s tests -q` and `bash tests/test_installers.sh`.
A real GNOME/libadwaita runtime check remains necessary for the new editor click behavior.
