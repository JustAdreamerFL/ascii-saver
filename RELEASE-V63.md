# ASCII Saver V63

## About, shortcuts, and reliable component versions

- GNOME HIG primary-menu button in the dashboard, with Preferences, Keyboard Shortcuts, Help, About, and Quit; System Information is kept separately.
- Standard keyboard shortcuts (Ctrl+, / Ctrl+? / F1 / F10 / Ctrl+W / Ctrl+Q).
- Uses Adw.AboutDialog and Adw.ShortcutsDialog where available; older libadwaita uses native-window fallbacks.
- System Information displays the running GUI's embedded version, installed release, bundled Rust renderer, native watcher version, detected backend, and running watcher identity.
- The watcher executables now support `--version` without launching the idle-service event loop. An installed `watcher-backend` marker records which backend was built.
- Checks `/proc/<pid>/exe` against the installed watcher inode, reporting a stale running executable as **Restart required** rather than guessing based on the PID filename.
- Additional CLI command `ascii-saverctl components` prints the same report without requiring GTK, useful for bug reports.

## Not changed

The GNOME Wayland pointer is **still reported visible** by the user on V62. This release does not claim a fix for cursor layering or Dash to Dock. The planned preference-sidebar redesign remains in the backlog.

## Testing limitations

Python source, test suite and installer syntax can be checked offline. Real libadwaita interaction, C++/Qt and C/GIO compilation, and the reported GNOME pointer behavior must still be verified on a live desktop.
