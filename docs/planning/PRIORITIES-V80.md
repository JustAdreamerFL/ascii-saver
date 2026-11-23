# ASCII Saver: user-reported priorities after V80

Based on `OBSERVATIONS-COMBINED.md`, `BACKLOG-V55.md`, `RENDERER-BACKLOG.md`
and the cumulative V66-V79 release notes. Code-level changes are not proof
that a defect is fixed in the user's running GNOME/KDE installation.

## P1: highest priority when runtime testing starts

- KDE Task Manager window identity and grouping (E02/B213): the standalone
  Playlist Editor had a generic Wayland icon or separate task entry; the
  Effect Library did not appear as an ordinary taskbar window. The right fix
  depends on observing actual processes, app IDs and compositor behavior.
- Confirm multi-monitor fullscreen, Escape/pointer dismissal, sync and shared
  versus independent scaling on KDE/GNOME; V67-V73 changed those paths but
  no full integrated live test has been done yet.

## P2: observed usability issues

- Preferences navigation and narrow window controls (B01/B02): V79 updates
  header width, compact navigation, Save/Discard and wide per-monitor rows.
  **Code change complete; visual test pending.**
- Effect Library and Playlist Editor context-local Save/Discard (E05): V74;
  gallery-first playlist editing (E01/E03/E04): V75. Live confirmation pending.
- Performance and measured durations (C01/B210): V76; preview layout
  (D01-D04): V77; Diagnostics/Artwork editor feedback (C02/C03): V78.
  Pending visual/behavioral validation.
- Monitor hot-plug: detected monitor count updates, and rows for per-monitor
  frame rate, artwork and palette are now reconciled on plug/unplug in V80,
  preserving disconnected saved and uncommitted values. **Code patched; real
  GTK4/Wayland hot-plug validation remains pending.**
- The Preview Behavior selector is present both in Settings and Effect Library
  (B214); consider simplifying the duplicate at a later UX pass.

## Do not work on without fresh evidence

- The old ~8% idle GUI CPU report appears to have disappeared; do not assume
  it is still broken without a new measurement.
- Watcher RSS, hypothetical deadlocks or launcher failures.
- Complex palette transitions, locked-screen integration or new renderer
  capabilities, which are ideas, not user-reported bugs.

## Workflow

Select a user-observed issue, inspect the latest code first, patch and add
regression coverage, ship a cumulative ZIP, and explicitly disclose the absence
of GNOME/KDE live validation. User-side testing is deferred until requested.
