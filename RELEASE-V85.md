# ASCII Saver V85 (0.85.0): responsive effect galleries and consistent empty-state UX

Date: 2026-11-08. Experimental source update; **GTK/KDE/GNOME Wayland layout is not verified**.

## Existing user-approved UX scope

The V53 and later feedback requested responsive Effect Library/Playlist Editor layouts that prioritize the animated gallery while keeping Search, filters, Play and contextual Save/Discard accessible. V79 made Preferences adaptive, but Effect Library retained a fixed three-column `Gtk.Grid`. Even a narrow resizable window still reserved room for three 205-pixel cards and its horizontal filter controls.

## Changed

- Replace Effect Library's fixed three-column `Gtk.Grid` with `Gtk.FlowBox` (one to three columns as space permits). Thumbnail buttons, checkboxes and dedicated Play buttons keep the same instances and callbacks when filters change.
- Place Effect Library's existing scrollable gallery and an explicit empty-results state into a `Gtk.Stack`. If no effect matches, show a searchable-empty message and **Clear filters**, not a blank gallery. The pinned preview remains below the expanding gallery region.
- At narrow widths, stack the library Search/duration/intensity controls and preview-mode/replay controls vertically. At the narrowest widths, also stack the contextual Save/Discard banner controls instead of clipping them.
- Apply the same narrow-width filter layout to Playlist Editor, where the navigation split already collapses.
- Give Playlist Editor's empty-filter state a **Clear filters** button, matching Effect Library. Clearing filters in either window updates all three selectors in one batch to avoid redundant thumbnail rebuilds. This changes only search/filter UI, **never the effect inclusion or saved playlists**.

## Regression checks

- New GTK-independent tests exercise filtering with mock FlowBox child wrappers, preserving selected card identities and original ordering through no-match and reset states.
- Test that clearing filters performs one gallery refresh and does not alter config values; check both windows' source breakpoint contracts and existing preview position.
- The source-level regression suite, installer and GNOME/KDE session-detection checks must pass before packaging. One GTK/VTE integration test may be skipped when its GI typelibs are unavailable.

## Still open

- **Not verified:** actual Gtk.FlowBox wrapping, `Adw.Breakpoint` transitions, Save/Discard overlay placement and in-window playback on narrow GTK windows under GNOME and KDE Wayland.
- KDE taskbar grouping after V84 and fullscreen/mixed-monitor renderer tests also require a real desktop session.
- More optional UX ideas and future features remain in `MASTER-BACKLOG.md`; none were silently added here.
