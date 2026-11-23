# ASCII Saver V88 (0.88.0): progressive photo conversion tools

**Date:** 2026-11-08. Experimental source build, not a validated GNOME/KDE release.

## Implemented

- Photo to ASCII now has a **collapsed Advanced image tools** expander. Beginners see the same V87 basic controls; opening Advanced reveals gamma (0.5–2.5), edge definition (0–100), and Floyd-Steinberg dithering. **Reset** restores neutral values without altering basic controls.
- Gamma changes intermediate tones while preserving pure black/white. The edge control applies local unsharp masking based on the neighboring sampled character cells. This is edge **definition**, not an edge-only art filter. Dithering distributes quantization error among later cells to render smoother tones with the selected ramp.
- Preserve whitespace padding when fitting images and do not spread edge contrast or dithering into the blank borders. Every output remains plain text with exactly the requested row and column count; all options are bounded by validation.
- All advanced controls use the same 80 ms debounced original/ASCII comparison as the basic controls. Export and editor insertion refresh pending adjustments before use. The original photo, existing artwork and saved filenames are unchanged until the user explicitly exports or saves.
- Update `ROADMAP.md`, `TASKS.md`, `MASTER-BACKLOG.md` and the dated `CHANGELOG.md`, retaining previous release notes.

## Still open

- Real GTK/libadwaita visual and keyboard accessibility checks on GNOME and KDE, including resizing, expander interaction and 120-column previews.
- Persistent reusable photo sources and conversion settings; exported `.txt` alone cannot reconstruct editing parameters. Other advanced tools, local asset search and licensed online artwork providers are not shipped.
- KWin window grouping, multi-monitor rendering, GNOME cursor and lockscreen behavior remain pending real-device validation.

## Verification

- Headless unit tests cover gamma at neutral and extreme tones, dithering reproducibility and character diversity, edge locality, whitespace padding, invalid input ranges and combined options.
- Full Python suite, installer/session tests, static compilation, all 37 effect packs and ZIP integrity are checked for this version.
- GTK/Wayland runtime and Rust renderer on the user's machine are **not tested** in this environment.
