# ASCII Saver V69 (0.69.0): reliable font fit on mixed displays

## Changes

- **Shared mode auto-fit is now functional**. When independent monitor settings
  are off, the fullscreen renderer calculates one common font size that fits
  the configured artwork on the most constrained active display. That size is
  applied on each monitor instead of silently disabling auto-fit.
- **Independent mode keeps its own size**. Every monitor fits the artwork it
  actually uses to its own grid. A landscape monitor no longer inherits a
  portrait monitor's smaller font in independent mode.
- **Auto-fit Off restores the configured font** on the next render. The
  renderer first resets VTE to the baseline saved font, then calculates fitting
  from baseline glyph geometry, never from the previously shrunk size.
- **Preferences exposes auto-fit in both modes** rather than hiding it inside
  the expanded independent section or silently turning it off when toggling
  independent settings. Its per-display estimates use every display's chosen
  artwork, not one monitor's artwork repeated on every display.
- **Configuration defaults are isolated**: each new configuration now owns its
  own palette, monitor dictionaries and excluded-effect list, avoiding changes
  to a previously loaded configuration leaking into future loads.

## Automated verification

- Pure-Python tests cover independent and shared fitting, different artwork per
  display, empty artwork, no monitors, explicit opt-out, and config isolation.
- Headless runtime tests execute the actual renderer font-fitting method with
  fake monitor geometry and fake VTE/Pango, including switching modes and
  restoring the configured font after a previous shrink.
- Existing source, integration, playback and release-asset checks remain.

## Limitations

No desktop compositor or GTK4/VTE runtime is available in the test environment.
The tests validate the logic and simulate the renderer method, but actual
font glyph metrics, first-map timing, compositor scale factors and hardware
hotplug still need an eventual end-to-end GNOME/KDE run. No manual testing is
required for this development iteration.
