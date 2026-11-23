# ASCII Saver V110 (0.110.0) | identity refresh

**Date:** 2026-11-23. Experimental source release. Real GNOME/KDE Wayland
window grouping and desktop integration still require on-device validation.

## Changes

- The GTK application identity is now `com.github.justadreamerfl.asciisaver`.
  The control panel, renderer, desktop entries, AppStream metadata and icon
  use the same reverse-DNS identity, avoiding generic icons and taskbar
  grouping mismatches.
- The fullscreen cursor D-Bus service and optional GNOME Shell extension use
  `com.github.justadreamerfl.asciisaver.Fullscreen`.
- The installer removes desktop entries, metadata, icons and autostart files
  from the previous `io.github.robbybobby77.AsciiSaver` identity. User
  configuration and artwork under `~/.config/ascii-saver` are preserved.
- The uninstaller removes both the current and previous desktop identities.
- Online installation and project links use `JustAdreamerFL/ascii-saver` and
  the manual **Release** GitHub workflow publishes generic and versioned
  archives with matching SHA-256 files.

## Validation

- All 677 offline unit/source-contract tests pass.
- Installer, upgrade, uninstall and online-bootstrap integration tests pass.
- Desktop entry and AppStream metadata validation pass.
- Live GNOME/KDE Wayland identity grouping remains open for confirmation.
