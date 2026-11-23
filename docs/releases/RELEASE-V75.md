# ASCII Saver V75 (0.75.0): Playlist Editor gallery-first redesign

This update addresses the user's reported E01/E03/E04 Playlist Editor usability
problems, especially the small scroll viewport, bulky generation forms and
inconsistent nested hover surfaces. No speculative renderer or idle CPU changes.

## What changed

- **Gallery first:** the main editor content is now a genuine expanding, scrollable
  animated-effect gallery. The selected playlist remains available in a padded,
  reorderable left sidebar. The content page is titled **Effect gallery** rather
  than **Playlist details**.
- **Secondary controls are opt-in:** the playlist name, enabled/shuffle settings
  and automatic/measurement-based generation live in one collapsed **Playlist
  options** panel. Opening it displays a bounded 200px scroll region instead of
  displacing most of the gallery. Playlist generation still edits the local
  draft only and requires explicit Save.
- **Better selection workflow:** adds case-insensitive search, preserves existing
  duration/intensity filters, shows the active playlist and selected/visible
  counts, and displays a friendly empty-filter result. Filters never change the
  playlist's selections.
- **Gallery card affordances:** enlarged sample previews, one selected-card
  outline, no duplicated pointer-hover border inside the thumbnail, distinct
  keyboard focus indication, and a separate explicit real-renderer Play button.
  Only visible sample animations are active as before.
- **Local Save/Discard** and desktop-adaptive split navigation from V74 remain.

## Verification

- Python headless tests: 332 passed, 1 skipped (GTK/VTE not installed).
- Added 7 filter, layout, and contract tests; updated the old V52 navigation
  contract from the obsolete "Playlist details" name to "Effect gallery".
- The change is **not verified in a real libadwaita window** or on KDE/GNOME
  Wayland. Actual responsive behavior, thumbnail hover and scroller sizing
  require the later user device test. This does not establish a runtime fix.

## Intentionally not included

- KDE taskbar grouping fix (requires a live Wayland check).
- Palette transition extensions or new effect engines.
- CPU, stability, or concurrency changes without a supporting user report.
