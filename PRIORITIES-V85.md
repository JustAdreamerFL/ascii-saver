# Priorities after V85

Date: 2026-11-08. Keep [TASKS.md](TASKS.md) as the short checked list and [MASTER-BACKLOG.md](MASTER-BACKLOG.md) as the complete issue register.

## UX source change just completed

- Effect Library uses adaptive 1–3-column FlowBox, matching Playlist Editor rather than requiring a three-column minimum width. Library and Playlist Editor filters stack on narrow windows; both have explicit Clear filters when no cards match. No new playback mode, watcher control or palette functionality was added.

## UX visual validation still required

1. Under GTK/libadwaita, resize library and editor from wide to narrow and back. Check search, dropdowns, preview controls, empty results, scrolling and contextual Save/Discard.
2. Confirm preview thumbnails and Replay stay usable, only visible thumbnails animate, no effect inclusion or playlist order changes merely from search/reset.
3. Verify V74–V84 design changes, especially large font sizes, playlist gallery/sidebar, banner positioning and diagnostics.

## Other open runtime checks

- KDE Task Manager grouping after V84.
- GNOME/KDE Wayland fullscreen cursor/dismiss, monitor hot-plug, auto-fit, palette differences and synchronization.

## Deferred by scope

Do not introduce unapproved palette collections, image palette extraction, alternate playlist automation, KScreenLocker replacement, optional watcher lifecycle controls, or speculative CPU/RAM optimizations.
