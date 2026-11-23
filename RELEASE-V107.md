# ASCII Saver V107 (0.107.0) | Preferences layout reset

**Date:** 2026-11-09. **Experimental source release, not a visually accepted GNOME/KDE build.**

## What changed

### A real narrow-window design

- Replaced five toolbar tabs, five-item bottom switcher and breakpoint-dependent fallback with one category dropdown in the native Adw.HeaderBar. All five sections remain available, and programmatic navigation synchronizes with the selector.
- Preferences' default size is 670 × 660 logical pixels and minimum requested size is 360 × 320. This does not guarantee that every compositor or theme can shrink to exactly 360 pixels, but eliminates the hidden tab widget's minimum-width pressure.
- Custom preference controls now stack their captions and controls **by default**. The view no longer depends on a narrow-width breakpoint being activated after its own content has already forced the window too wide. Per-monitor frame-rate, color and artwork widgets use the same stacked rows.
- In Appearance, the color transition direction and blend-step controls remain available in a collapsed **Color transitions** expander; cycling toggle and palette colors remain visible.

### Separate preferences from live status / actions

- Removed Renderer and Idle watcher process rows from Preferences. These remain live on the **main Dashboard**, which still polls their state.
- Removed two Diagnostics buttons, file actions, explanatory filler and permanent notice rows from Preferences. Moved their useful entrypoints to **main menu > Tools**: Edit Artwork, Performance History, Measured Effect Durations and Run Diagnostics. Existing CLI `ascii-saver doctor` still works.
- Replaced permanent “Changes saved” footer with a hidden clean state. Save/Discard appears only when the page actually has unsaved changes, below the content rather than over it. Long operation errors appear as GTK toasts rather than occupying Settings rows.
- System Diagnostics window now relies on one native titlebar close button and supports Esc.

### Functionality preserved

- Five Preferences categories, configuration read/write, Save/Discard, per-monitor overrides, palette cycle and ping-pong, preview/playlist modes, gallery, performance measurements, diagnostic checks and default artwork editing are still present.
- No changes to the Rust renderer, watchers, palette algorithms or format of user configuration.

## Testing

- `python3 -m unittest discover -s tests -q`: headless regression suite including new V107 contracts.
- `python3 -m compileall -q .`, installer and session detection tests, and asset validation.
- A GTK/libadwaita desktop runtime was **not** available in this execution environment. New layout is not claimed to have been visually verified at 360, 420, 600 logical pixels, or on actual GNOME/KDE Wayland.

## Manual acceptance criteria on Fedora/GNOME and KDE

1. Run `./install.sh`, completely exit previous GUI process, then `ascii-saver preferences`.
2. Make window narrow (roughly 360–420 **logical** pixels) and tall. Check no settings, action buttons, numeric reset controls, per-monitor artwork picker, palette swatches or title controls clip off the right edge. Check scrolling is vertical only.
3. Use category dropdown to visit General, Appearance, Displays, Animations and Preview, then open one directly using dashboard navigation. Selector must track the active section.
4. General should start with activation settings, no renderer/watcher statuses, diagnostic cards or “Changes saved” strip.
5. Edit a setting, confirm Save/Discard appears below content; Discard reverts without saving; Save hides it. Make sure controls can be edited with keyboard.
6. Open `ascii-saver` > menu > Tools and verify artwork editor, performance graph, measured effects and diagnostics still work; Esc closes diagnostics.
7. Open Appearance > Color transitions, edit values, Save/Discard, reopen Preferences and confirm persistence; test independent palettes on displays where configured.
8. Test font chooser and per-monitor artwork editing at narrow width; if anything clips, capture a full-window screenshot and `GDK_DEBUG=...` logs as available.

**HIG references:** https://developer.gnome.org/hig/guidelines/adaptive.html and https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/adaptive-layouts.html
