# KDE ASCII Saver V56 — preview lifecycle, artwork editing and synchronized preferences

This release follows the user's real-world V55 testing on a two-monitor KDE Plasma Wayland desktop.

## Implemented

- **Main-window Preview cycles effects.** Windowed preview now has an explicit `PreviewSequence` cursor, independent of the fullscreen screensaver. It advances after a successful effect and retains the configured final-artwork hold. In random mode it shuffles the enabled effects without repeating one until the bag is exhausted; in playlist mode it follows the configured playlist scheduler. One enabled effect necessarily repeats. This does not turn the windowed preview into a second fullscreen multi-monitor screensaver.
- **Per-monitor Edit Artwork uses a built-in editor.** The button opens the exact selected config artwork, or `logo.txt` when the default is selected. The Adwaita editor shows its contents in a monospace text view; the Save action writes UTF-8 atomically and reports errors. This avoids depending on desktop `.txt` file associations or external editors. The original artwork remains intact unless Save is pressed.
- **Immediate dashboard refresh on Save.** The already-open main window refreshes when Preferences finishes saving, rather than waiting for its periodic poll. The success toast now reads `Saved.`.
- **Auto-fit is available only for independent monitors.** Disabling independent settings also deactivates auto-fit; its control is located inside independent monitor options. The renderer additionally ignores any stale `auto_fit_artwork=true` value in configurations with `per_monitor=false`. This avoids the unsupported combination associated with the user's crash at large font sizes. In shared mode a manually selected font size is used on both screens and can clip. This is a conservative UX/safety change, not a claim to have diagnosed the underlying VTE crash.
- The Rust `ttfx` source and native KDE watcher are unchanged. V55's persistent Cargo cache is retained.

## Checks

- Python unit tests, including new pure-Python preview and editor I/O tests.
- Installer regression tests and shell syntax.
- Source archive content and integrity.

## Still open

- Palette enforcement of effect-generated ANSI truecolor and meaningful transitions between separate user palettes.
- Full two-monitor preview instead of one resizable window.
- Root-cause analysis of the reported large-font shared-display crash, using the persisted renderer log.
- Playlist editor redesign, per-window Save/Discard, better performance charts and taskbar grouping.
- Watcher memory measurement (RSS vs PSS; approximately 46 MB observed by the user).
- Live KDE/GTK runtime testing, including in-place artwork editor and preview process changes.
