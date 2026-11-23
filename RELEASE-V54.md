# KDE ASCII Saver V54 — Usability fixes from V53 feedback

Version 0.54.0. **Experimental:** GTK4/libadwaita runtime behavior must still be tested on the user's CachyOS desktop.

## Changes implemented

1. **Factory reset buttons:** Every numeric setting in Preferences, including advanced animation timing, effect hold, idle delay, global/per-monitor FPS and palette steps, has a contextual restore-default icon. It appears only while the value differs from the immutable application default; resetting a previously saved custom value is tracked as an unsaved edit. Timing defaults: all multipliers and simulation hold = 1; FPS = 60. Sliders show their values above rather than on the right.
2. **JSON editing:** Raw playlist JSON opens in a standalone text editor window with validation and explicit Apply to Preferences. Normal users should use the visual editor instead.
3. **Adaptive categories and Save/Discard:** Removed duplicate titlebar Save action. The floating, non-layout-shifting banner is the single Save/Discard surface, with a solid Adwaita window background. At very narrow widths, header category dropdown replaces overflowing category tabs.
4. **Per-monitor artwork picker:** Text art can be selected through GTK FileDialog. Chosen .txt files are imported without overwriting into `~/.config/kde-ascii-saver/artworks/`, with editable files and safe relative `artworks/name.txt` references. Legacy root-level references remain supported.
5. **Artwork fitting:** Each animation begins with the configured font instead of compounding previous shrink operations. When fit is disabled, that font is left untouched. When enabled, independent mode uses per-monitor estimates; shared mode computes one size from the smallest display. Fit warnings explain the selected mode and report monitors separately. This policy is implemented but needs physical display testing.
6. **Measurement history:** Measured-effect duration view uses native `Adw.PreferencesPage` and `Adw.PreferencesGroup` sections, with individual effect rows, median durations, min/max, run count and a display selector. Preliminary results are marked.
7. **Dashboard:** Renderer and watcher status now occupy separate rows, Stop is disabled when no renderer is running, and command feedback uses short Adwaita toasts rather than ever-growing inline text.
8. **Persistent main Preview:** Input events no longer dismiss the windowed renderer (full-screen screensaver still dismisses). First-frame caret flash and preview end caret mitigated with VTE hide-cursor escape, requires desktop confirmation.
9. **Settings feedback:** Save toast now explains idle watcher reload on its one-second polling cycle and that new effects pick up the settings on next launch.
10. New GTK-free tests for default values, monitor fit strategy, artwork import / config roundtrip, measured view grouping, and installer assets. Includes scripts/diagnose-ui-cpu.sh for troubleshooting the *unproven* idle CPU root cause.

## Outstanding from Round 1 and Round 2

- Full playlist editor UX redesign (gallery first, native Adwaita sidebar, proper dirty-state actions in the editing window).
- Grouping/transient and taskbar identity of secondary windows on KDE Wayland.
- Full performance graphs overhaul with meaningful axes, units and data provenance.
- Effect-library cards unified with playlist selection/hover structure, classification labels, replay and preview alignment.
- Actual idle CPU root-cause diagnosis (reported ~8% on user machine).
- Distinct Start/Stop Idle Watcher service controls and action semantics.
- Artwork editing completion event / diagnostics modal UX.
- Real renderer-level issues and per-monitor fit runtime verification on portrait + landscape displays.
- Random playback behavior, palette progression and full native KDE lock-screen integration.

**Source limitations:** No libadwaita/PyGObject runtime in the build container. Source syntax, offline tests, archive and installer shell checks are not substitutes for a desktop test. No Rust engine modifications have been compiled here.

See `OBSERVATIONS-ROUND-1.md`, `OBSERVATIONS-ROUND-2.md` and `RENDERER-BACKLOG.md` for the full backlog.
