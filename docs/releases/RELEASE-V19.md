# V19: Artwork layout preservation

This release fixes the completed-artwork fallback so it centers a multi-line logo as one visual block rather than independently centering each line. It preserves relative indentation and trailing whitespace, expands tabs at eight-column stops using terminal-cell widths, strips control characters, and clips rows/columns. This matters when an animation has finished and the monitor is waiting for the synchronized transition barrier.

## Testing
- 10 targeted final-frame regression tests passed.
- Python compilation and bash installer/uninstaller syntax checks passed.
- Full unit-suite: 71 tests executed with one import error (`gi` missing in this environment); no assertions failed.
- No KDE Wayland, Gtk/VTE or KWin runtime testing was performed.

## Remaining requirements
True time scaling separate from FPS pacing, inline animated previews, reliable per-process GPU/FPS instrumentation, native KDE lock-screen integration and verification of activity inhibition on actual Plasma remain unfinished. Uninstall cleanup for the KWin activity-detection script also requires validation.

Run `bash install.sh` only on a test desktop after backing up `~/.config/kde-ascii-saver`.
