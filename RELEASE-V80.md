# ASCII Saver V80 (0.80.0): hot-plug-aware monitor preferences

This development release addresses a source-verified issue recorded after V79:
Preferences updated the connected-display count but did not refresh its
per-display FPS, palette and artwork controls when monitors were attached or
removed during the lifetime of an open Settings window.

## Changes

- Listen to the existing GDK monitor-list `items-changed` event and reconcile
  FPS, palette and artwork rows for newly attached and disconnected displays.
- Read initial per-monitor values for *new* displays from config, with the
  existing shared FPS/palette as fallback.
- Reuse the same control objects when a display reconnects with its same
  connector key. This retains its uncommitted edits and avoids duplicate
  signal subscriptions or duplicate rows.
- Register dirty-state listeners on dynamically created controls so their
  edits can be saved and discarded just like initially connected displays.
- Extend the saved form baseline only for *new* display defaults. Merely
  plugging in a display should not mark the form dirty, and existing unsaved
  edits on other controls must remain pending.
- When saving Preferences, merge the per-display FPS, palette and artwork
  mappings with already saved entries. A disconnected display's persistent
  settings must not be deleted just because it is absent from the current UI.
- Preserve the V79 responsive layout and existing per-display behavior.

## Verification

- 370 Python tests passed; 1 GTK/VTE-dependent test skipped in this headless
  environment. Includes 10 new V80 tests covering config merges, baseline
  reconciliation and the actual GTK-independent row-reconciliation method.
- Installer and session-autodetection shell tests passed. Syntax checks and
  the 37 packed effect assets passed.
- Real GTK4/Wayland monitor attach/detach, connector identity stability,
  alternate app/compositor environments and UI layout have **not** been
  validated on a GNOME or KDE desktop. No runtime fix is claimed confirmed.

## Not changed

No speculative CPU optimizations, watcher changes, renderer rewrites, advanced
palette-transition behavior or KDE taskbar fixes were added.
