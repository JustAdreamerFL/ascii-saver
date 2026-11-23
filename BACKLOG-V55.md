# KDE ASCII Saver V55: backlog and testing requirements

## User-observed bugs, high priority

- **Auto-fit with font size ~52 crashes the fullscreen renderer**, especially independent displays + auto-fit ON. Must obtain the actual renderer stderr / exit status and test live on mixed orientation displays. No proven fix yet; the renderer now saves stderr into `~/.cache/kde-ascii-saver/renderer.log` for post-start crash investigation. Monitor auto-fit OFF is reported to leave artwork shrunk on both displays; verify whether GTK settings were saved/restarted and actual VTE geometry.
- **Palette change is not applied to effects' ANSI RGB content.** Per-monitor palettes and transitions appear ignored. Need Rust renderer color-map support for ANSI/RGB, and multiple *distinct palettes* with transition exclusively between effects, preserving renderer final-frame colors. Not resolved by V55.
- **Very narrow Preferences hides top-level window controls.** V55 attempts to reduce the intrinsic width of the header's category dropdown; verify on actual libadwaita, including minimum supported width.
- **Standalone watcher reports ~46 MiB idle memory in user's monitor.** Distinguish RSS from PSS and private memory in `/proc/$pid/smaps_rollup`; inspect which Qt/KF6 libraries are shared before optimizing. Use `scripts/diagnose-ui-cpu.sh` with the watcher running; avoid attributing the full RSS to private usage. Idle GUI CPU ~8% issue is currently not reproducible by user; reopen only with new evidence.

## UI remaining

- Per-window Adwaita Save/Discard for Effect Library and playlist editor, with correct discard of underlying settings.
- Full playlist editor redesign, large preview-first gallery, consistent Adwaita cards, window grouping in KDE task manager.
- Separate preview window centering, resize behavior, replay, no unnecessary explanatory text.
- Performance history redesign with meaningful axes and units, monitor separation, no scrolling glitch.
- Dedicated Diagnostics view with Copy/Clear and artwork editor completion detection based on saved file changes and editor exit.
- Correct grouping and taskbar identity for Effect Library, measurements, playlist windows.
- Stable sizing across all fonts and screen orientations, including minimum fit rather than clipping.

## Later / feature wishes

- Image-to-three-color palette extraction; selectable curated themes including possible Omarchy-inspired palettes (respect artwork licenses).
- Extend palettes beyond one three-color set and support safe transitions between them.
- KScreenLocker wallpaper integration without disabling authentication remains the final major milestone.

## V56 follow-up from V55 hands-on testing

- Main-window preview repeatedly replayed the same effect instead of the whole sequence: separate `PreviewSequence` added, verify actual VTE full-run completion and configured hold on user's desktop.
- Per-monitor Edit Artwork did nothing: replaced external file association with built-in Adwaita text editor, live UI test pending.
- Preferences Save toast desired with punctuation: `Saved.`; direct refresh of main-window status was added.
- Auto-fit only worked with independent monitor settings and large fonts sometimes crashed with independent mode disabled: V56 makes auto-fit dependent on independent mode and skips auto-fit in shared mode. Root crash remains unverified; when reproducing inspect `~/.cache/kde-ascii-saver/renderer.log` and monitor resolutions/font dimensions.
- User reports successful new per-display font fit and no crash in independent mode; preserve this behavior.
- User reports low GUI CPU load now; leave original 8% report marked as not currently reproducible.
- Confirmed V55 functions: Preview/Close Preview control, reset buttons without UI shifting, per-monitor artwork selection/reset and Cargo-cache build speed.
