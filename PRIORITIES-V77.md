# ASCII Saver: prioritized USER-OBSERVED issues after V77

This is the active development queue. Source of truth: `OBSERVATIONS-COMBINED.md`,
`BACKLOG-V55.md`, `RENDERER-BACKLOG.md`, `UX-ROADMAP.md`, plus V56-V77
release notes and subsequent user feedback. **Do not invent stability issues to
fill a milestone.** A source-code change is *not* a confirmed runtime fix until
it has been checked on the user's real GNOME/KDE sessions.

## Critical / blocking, only when currently reproducible

- **Old auto-fit crash with large fonts (~52 pt), mixed-orientation displays**
  (`BACKLOG-V55`, B206-B208): the user originally reported a crash.
  V56 later reported independent auto-fit working and no crash; V69 further
  changed fit behavior. **No new report of a crash. Do not chase this blindly.**
  If it recurs, prioritize reproduction with the existing renderer log.
- **Settings lost across window interactions (E05)**: the Playlist Editor
  previously invoked a *full* Preferences reload on exit, overwriting other
  unsaved form edits. V74 changes this to a playlist-only refresh and preserves
  conflicting unsaved raw playlist JSON. Pending live validation.

## P1: real usability and workflow problems

1. **Save/Discard at the place where edits are made (E05).** V74 implements
   local unsaved banners in Effect Library and Playlist Editor. Effect Library
   writes only `exclude_effects` and `effect_preview_mode`; independent pending
   Preferences edits remain pending. The Playlist Editor now supports Discard.
   **Implementation complete; Wayland/GTK live verification pending.**
2. **Playlist Editor layout (E03, E04, E01):** V75 implements a gallery-first
   editor with search, larger cards and bounded, collapsed options. **Code
   complete; actual sizing and pointer behavior on Wayland unverified.**
3. **Window identity/taskbar grouping (E02, B213):** Playlist Editor is its own
   process/application ID and the Effect Library is a transient preferences
   child. KDE taskbar behavior needs a real Wayland check. Avoid speculative
   app-ID changes that could redirect activation to the wrong process.

## P2: improve reported but nonblocking behavior

- **Adaptive Preferences (B01, B02):** very narrow windows can obscure controls;
  some improvements landed in V54-V55. Confirm supported minimum sizes.
- **Measurements and performance graphs (C01, B210):** V76 replaces the raw
  diagnostic text with per-monitor native rows, adds a separate GTK/VTE group,
  monitor legends and independent axes. Code complete, pending live GTK/Wayland
  validation of layout, values and legibility.
- **Preview layout (D01-D04, F01, B214):** V77 centers both live preview
  canvases and adds in-window Replay, removes duplicated Close/help text,
  increases pinned height, and makes library thumbnails toggle selection.
  **Pending real GTK/Wayland verification** for resized windows. Preview-mode
  selection is still mirrored in Preferences and Library (B214), to simplify later.
- **Diagnostics/editor feedback (C02, C03):** dedicated readable diagnostic
  results; report completion only on actual file save/editor close.
- **Hot-plug monitor options:** current display count updates, but per-monitor
  FPS/artwork/palette control rows are not rebuilt on hotplug.
- **Watcher memory report (~46 MiB RSS):** not an observed functional failure.
  No optimization until proportional/private memory data warrants it.

## Already addressed in code, not yet verified by user

- Main persistent preview vs activity-dismissed saver (A03, V56).
- Random and ordered playlist selection (F02, V68).
- Shared and independent auto-fit rules, off restores configured font (B206-B208, V69).
- Between-effect palette phase and palette authority over effect RGB (V70-V71).
- Palette-aware animated sample thumbnails (V72).
- Text cursor / final frame in previews (T01/T02, V66-V67/V73).
- Original ~8% GUI idle CPU (A02): user later reported it apparently gone;
  leave unprioritized unless measurement shows a recurrence.

## P3: ideas, not bugs

- Multiple separately named palettes, complex cross-palette transitions,
  theme libraries and image-derived palettes.
- Secure lock screen integration without bypassing authentication.
- Broader renderer performance changes without user reports.

## Process for next release

1. Select one outstanding **user-observed** P1 or P2 issue.
2. Verify whether newer code already addresses it before changing anything.
3. Implement the smallest coherent fix and add regression coverage.
4. Run static/headless tests now; bundle versions cumulatively.
5. Reserve full-screen GTK/VTE, monitor geometry and KDE taskbar validation for
   the later joint device test. Keep unverified status explicit.
