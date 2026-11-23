# ASCII Saver V70 (0.70.0): predictable palette transitions

## What's fixed

- Fullscreen colors use the **synchronized animation round**, so all displays
  remain on the same point in their palette progress, even if one monitor's
  subprocess fails and is retried. A retry does not skip a palette color.
- The windowed, persistent preview keeps **its own** palette round, and changes
  color only after a successful effect completes. Launch failure / animation
  failure retries keep the current color.
- Independent palettes remain independent: monitors may have different color
  sequences, but advance together after the barrier that waits for all displays
  to finish their animation and hold. A display without a custom palette uses
  the shared palette.
- A preview uses the global/shared palette, not a special display override.
- User-supplied 6-digit RGB colors with harmless whitespace around them are
  normalized before interpolation. A malformed per-monitor palette falls back
  gracefully instead of crashing the renderer.
- The standalone `palette_engine.py` is included in the installer.

## Verified automatically

- Pure Python unit tests cover RGB mixing, wrapping, palette-off, custom
  displays, shared fallback, whitespace, empty/bad settings, and round reuse.
- GTK-free integration tests execute the real `_tte_argv` method with a fake
  VTE terminal, verifying which foreground color the renderer actually sets.
- Existing tests, shell installer checks and all 37 preview asset checks run.

## Known limitations

The foreground palette is the VTE **default foreground**. Some effects emit
explicit ANSI/RGB colors and intentionally override it; this release does not
recolor effect-generated RGB output. This fix concerns cross-effect color
selection and reliability, not within-effect gradient animation.

A real GNOME/KDE session with GTK4/VTE and Wayland is not available here. Runtime
behavior on the user's dual-monitor setup is intentionally deferred for a
later testing round; no user action is needed now.
