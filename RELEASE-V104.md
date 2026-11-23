# ASCII Saver V104 (0.104.0)

## Multi-monitor cohort starts and palette round safety

V104 changes the core fullscreen GTK/VTE renderer's start scheduler. It does
not add controls or make changes to Artwork Studio.

- **Single next-round timer:** Once every active fullscreen monitor finishes
  its animation and its own final-frame hold, the shared barrier advances
  the playlist, effect and palette round exactly once. It now schedules one
  GTK main-loop callback to launch the entire monitor cohort rather than
  scheduling a separate restart for each monitor.
- **Grouped first launch:** Fullscreen windows initially created for all
  connected monitors now use one delayed cohort start. A newly hotplugged
  monitor can join the current round without relaunching displays already
  playing. Windowed Preview retains its independent start timer, selection
  sequence and color clock.
- **Stale timer protection:** Every cohort callback carries its intended
  shared round. If a monitor was removed, the application shut down, or the
  playlist advanced before the timer ran, that callback cannot start a
  removed window or a renderer using an obsolete palette round.
- **No change to palette settings:** V103's optional ping-pong palette, per-
  monitor palette overrides and their interpolation settings remain intact.
  Color remains selected for each effect at its launch, not during frames;
  different monitors can show different colors in the same shared round.

## Verification

- 593 Python tests (592 passed, 1 skipped), including eight new simulated
  multi-monitor cohort/round/hotplug tests. Updated the earlier V67 and V68
  fake GTK test contracts to account for the new deferred cohort callback.
- Headless installer, desktop detection and effect pack checks are run for
  each release before packaging. See the terminal logs if inspecting the
  development environment.
- No actual GTK/GNOME/KDE/Wayland compositor sessions, physical monitors or
  Rust renderer build have been validated here. A single GTK callback reduces
  scheduling skew but **does not guarantee frame-perfect simultaneous output**:
  individual VTE child spawn times, compositors and monitor refresh rates vary.

## Next

1. On-device fullscreen tests with two different refresh rates, monitor
   hotplug during an effect and during its final-frame hold, and palettes
   with `shared_effect` on and off.
2. Watcher inhibitor behavior during games/videos and real measured idle
   CPU cost, without asserting unverified fixes.
