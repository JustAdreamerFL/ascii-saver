# ASCII Saver 0.68.0: independent playback history and synchronized rounds

## Fixes

- Fullscreen and windowed preview now construct **separate playlist schedulers**.
  Previewing a sequence never consumes the fullscreen scheduler's next effect.
  Both sequences begin at the first enabled playlist effect and each advances
  only after its own successful completion.
- Each fullscreen monitor has its own randomized **shuffle bag** for unordered
  effects. A bag plays each enabled effect once before refilling, avoiding
  accidental immediate repeats between bags. This preserves independent
  monitor animations without changing synchronization timing.
- An explicitly selected playlist or shared effect still has priority over
  the unordered bag; exclusions are respected. Changing the set of eligible
  effects resets that monitor's bag.
- Shuffled *playlists* now avoid repeating the same effect at a cycle boundary
  when at least one different eligible effect exists. A one-effect playlist
  intentionally repeats its one effect.

## Verification

- New headless tests verify that two playlist cursors are isolated, per-monitor
  random rotation does not repeat prematurely, explicit priorities and
  exclusions are preserved, and the existing multi-monitor hold barrier waits
  for all active displays before starting the next round.
- Previous tests, installer shell tests, Python compilation and packaged
  asset checks are included in the release validation.

## Not verified here

This environment has no GTK4/VTE/Wayland compositor or Rust engine toolchain.
Real per-display focus, launch timing, font fitting, animation rendering and
monitor hotplug must still be validated on GNOME/KDE. No manual action is
required to continue development, but those features must not be considered
runtime-verified.

## Remaining priorities

- Verify auto-fit on mixed portrait/landscape displays, including turning it
  off after a previously scaled animation.
- Diagnose compositor-specific preview and fullscreen lifecycle failures.
- Profile idle GUI CPU cost; revisit window/palette layout only after basic
  functionality is reliable.
