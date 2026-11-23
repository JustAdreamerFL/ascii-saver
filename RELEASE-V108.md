# ASCII Saver V108 (0.108.0) | stabilization release

**Date:** 2026-11-09. Experimental: headless-source regression verified; **not** visually or interactively validated on GNOME/KDE Wayland.

## Scope and actual changes

- **Palette editing:** A dynamic, bounded set of 1–8 foreground colors replaces three fixed swatches. Add color, Remove last and Restore default palette actions update the same editable state and participate in Save/Discard. The Reset button immediately reflects manual swatch edits. Background has its own factory reset. Separate **Different palettes on each display** is independent of independent FPS/artwork settings, with per-display Add/Remove/Reset. The shared palette remains the fallback for unmatched displays and windowed Preview.
- **Renderer color behavior:** Palette engine remains deterministically indexed by completed effect/monitor round, defaulting to cycling for multi-color palettes; users may explicitly choose static. `palette_steps=1` cycles on each successful effect; higher values blend across multiple effect transitions. **Color editing does not recolor an already running terminal frame; Save and subsequent effects are needed.**
- **Local artwork history:** My Artwork offers **Recently used**, a private bounded list of artworks actually launched by the renderer since V108. It includes the editable default `logo.txt` and stored artwork files, in most-recent-first order. It does not claim to reconstruct use before V108; no background scan or remote upload occurs. History is stored under the user's ASCII Saver configuration directory.
- **Editor usability:** Open in drawing mode when compatible. Enable mouse click, continuous/interpolated drag strokes, eraser and the existing grid/zoom and keyboard controls, keeping the same text buffer and grouped Undo/Redo. Painting/erasing a selected text region now modifies just its printable cells while preserving line breaks. Text mode remains reachable. **Drawing precision under scaling and GTK gesture coexistence still require a live test.**
- **Online Surprise Me:** Select a different matching artwork when available, move it onto the loaded first page when it would otherwise be invisible, select its row and update the actual preview. Preserve pagination and filters.
- **Windows/Preview:** Windowed renderer uses an Adw.ApplicationWindow, its installed application ID and an Adw header/title "ASCII Saver · Preview". Escape, Ctrl+W and Ctrl+Q close Preview without dismissing it on ordinary pointer activity. Add matching close shortcuts to transient tools including Effect Library and measurement history. Existing close-request protection remains authoritative for editors with unsaved edits.
- **Effect Library:** Open transient to Preferences instead of competing for the primary application window position. Center an inline VTE preview inside a fixed-width child in a scrolled viewport, and remove that child when preview stops. Filter dropdowns in Effect Library and Playlist Editor receive an explicit minimum width, share available space, and use centered GTK list-item factories for both selected and popup labels.
- **Preferences:** Distinguish global and independent-display palette controls. Restore default colors, reduce redundant explanatory paragraphs, and hide the clean-state "Changes saved" footer. Keep a context-only Save/Discard bar. Use an existing wide breakpoint at 900sp for horizontal control layouts; compact settings continue to stack vertically.

## Compatibility

Preserves V107's unified `ascii-saver` commands, old launcher aliases, existing effect packs, Settings/JSON format and saved static palette mode. Additional modules bundled by `install.sh`: `palette_editor_model.py`, `artwork_history.py`, `artwork_selection.py`, `window_shortcuts.py`.

## Validation

- Python unit suite: **649 total, 648 passing, 1 skipped** (includes 25 new V108 tests of pure palette operations, actual local history files, Surprise selection and source UI contracts).
- Installer, desktop/session detection and effect archive checks executed separately in the release workflow.
- The `gi`/libadwaita runtime is not installed in this build container. **No live graphical build, GNOME/KDE Wayland test, or Rust renderer build** is claimed. All previous user-reported visual and pointer issues require on-device re-check. GTK changes are in source and may still expose runtime integration bugs.

## On-device acceptance (Fedora first)

1. Close old Dashboard/Preferences processes, update via `./install.sh`, launch `ascii-saver preferences` and compare short/long widths. Ensure no clipped controls and no clean footer.
2. On Appearance, edit existing swatch and Reset, Add/Remove, Save, reopen, then enable independent display palettes. Confirm a different color after a **completed** effect; choose steps=1 for clear successive colors.
3. Open My Artwork, switch to Recently used after an animation has launched, then open an artwork, Draw with click/drag, select and paint text, Undo and Save.
4. In Browse Online, click Surprise Me repeatedly on a large collection and verify each highlighted row matches the Preview. Verify no network claims beyond the actual remote result.
5. Open the Effect Library, check it doesn't displace Preferences in task switching, center its inline preview, verify Escape; open full Preview and verify title, grouping and Esc / Ctrl+W / Ctrl+Q. Check unsaved editor close confirmation.
6. Inspect filter dropdown label widths and centered entries at narrow and wide widths; check KDE as a second compositor.

## Remaining follow-up

Real interactive GTK acceptance, keyboard focus with an open color chooser, freehand precision at high DPI, history semantics for playlist-specific artwork, and long-running renderer / watcher inhibition tests. These are not declared solved by unit tests.
