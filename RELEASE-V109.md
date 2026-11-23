# ASCII Saver V109 (0.109.0) | usability repair

**Date:** 2026-11-09. Experimental source release. **No real GTK/Wayland GUI session tested here**; the user-reported Fedora visual failures must be rechecked on-device.

## Changes

- **Original effect RGB colors can be preserved.** New Appearance switch **Override effect RGB colors**, on by default for compatibility with prior releases. Off means all fullscreen/standalone Preview, Effect Library pinned preview, and Effect Library separate-window preview omit the Rust renderer `--no-color` option. ANSI/RGB colors emitted by ttfx are therefore preserved. The palette is still the terminal's foreground fallback for colorless content. Both switch states survive config Save/Discard and process restart; invalid stored values revert to the previous default.
- **Responsive Preferences navigation.** One compact DropDown for narrow widths, synchronized with a labeled left sidebar at 900sp and wider. Page selection stays in sync without a wide header widget forcing horizontal overflow. General, Appearance, Displays, Animations, Preview and Tools are retained.
- **Readable timing sliders.** Layout remains vertical at all widths; Gtk.Scale takes available row width and shows its value at the right. Removed cluttering end labels/marks and the old breakpoint that squeezed controls next to long descriptions. Existing numeric Reset controls remain present.
- **All Tools inside Preferences.** A dedicated Tools page contains Effect Library, Playlist Editor, Edit Artwork, Performance History, Measured Durations and Diagnostics. The dashboard links directly to Preferences/Tools instead of duplicating tool rows. The main menu no longer repeats the Tools section. The Preview page retains the explicit Library preview-mode setting.
- **Reliable keyboard closing intent.** Explicit Esc/Ctrl+W/Ctrl+Q handlers are installed for Preferences, Playlist Editor, Artwork Editor and other windows using the shared helper. The GTK key controller now runs in the capture phase so focused TextView, list and other child controls do not swallow closing keys. Existing unsaved-artwork and unsaved-playlist `close-request` protection still gets to decide whether the window actually closes. Playlist JSON editor gains the same handler.
- **Explicit artwork editing modes.** Show **Text** and **Draw** as grouped ToggleButtons, rather than an ambiguous single Draw toggle. Compatible single-column artwork, including Unicode box-drawing symbols, defaults to Draw, and the existing canvas/brush/eraser/freehand gestures remain bound to the drawing area. Text view can be selected directly. This improves mode discoverability but is **not** proof of on-device mouse gesture behavior.
- **Effect Library inline preview.** The fixed-height viewport and scrollable effect gallery remain; the inline VTE host is centered vertically and horizontally within the available preview slot while avoiding unbounded expansion that steals gallery height.

## Compatibility

- Existing saved settings and artwork are preserved; no migration of config files is necessary.
- `override_effect_colors` defaults to `true` for older configurations, preserving V108 colors unless changed. Unlike `cycle_palette`, this determines whether Rust-generated RGB colors are suppressed.
- All six Preferences sections and all saved numeric controls remain reachable; no new bundled Python module is required.
- The consistent `ascii-saver`, `ascii-saver preferences`, `ascii-saver preview`, and `ascii-saver stop` launchers remain unchanged.

## Automated validation

- Headless Python suite **669 tests total, 668 passing, 1 skipped**, including 20 new V109 pure-model and source wiring checks, plus updated legacy Unicode canvas cases.
- `bash tests/test_installers.sh`, `bash tests/test_session_detection.sh`, `python3 scripts/check-release-assets.py`, `python3 -m compileall -q .`, `bash -n install.sh uninstall.sh` and ZIP integrity/cumulative file checks are run in the release workflow.
- Rust `ttfx` **not rebuilt**: cargo/rustc unavailable. `gi`/GTK4/libadwaita **not installed** in this container. Actual Preferences resize, video/preview RGB playback, child-window shortcuts, canvas gestures and exact VTE vertical centering remain unverified.

## Manual Fedora validation

1. Close old GTK windows, install/update via `./install.sh`, run `ascii-saver preferences`. At about 360, 600, 900 and 1200 logical pixels check that compact selector turns into sidebar and no sliders or labels clip. All Tools should be in Preferences.
2. Appearance: switch off **Override effect RGB colors**, Save, close and reopen, verify the switch is still off. Use an effect that actually emits RGB colors, compare its live Preview with switch on/off. Confirm another completed effect does not undo that saved choice.
3. Open Effect Library in Tools. Use pinned live preview and verify VTE visual artwork centered vertically and horizontally without loss of scrolling. Repeat with separate window and original RGB enabled.
4. Open Playlist Editor, Preferences, Artwork Editor, and raw Playlist JSON. Press Esc and Ctrl+W; verify close or unsaved-change confirmation rather than silently losing changes.
5. Edit a compatible ASCII or box-drawing artwork. Verify **Text** and **Draw** exist; Draw brush clicks and freehand drags affect canvas, Text allows typing, then Undo/Redo and explicit Save preserve content.
6. Repeat in KDE Wayland when practical. No source-only test is proof of KDE or GNOME compositor behavior.
