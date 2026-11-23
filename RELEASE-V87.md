# ASCII Saver V87 (0.87.0): Photo to ASCII, first working converter

**Date:** 2026-11-08. Experimental source build, not a validated GNOME/KDE desktop release.

## Implemented

- **Photo to ASCII** is available from every native Edit Artwork window. Choose a local PNG, JPEG, WebP or BMP. The file remains untouched; input files over 25 MB or images over 60 megapixels are refused, and decoding is scaled to a maximum preview of 1200 x 1200 pixels.
- A pure-Python pixel converter maps RGB or RGBA images to terminal characters, composites alpha on white, handles padded rows, corrects the physical character width-to-line-height ratio (default 0.52) and lets the user choose **center crop** or **fit with whitespace**.
- A live side-by-side photo/ASCII comparison automatically becomes vertical below 770sp. Output updates after a brief 80 ms debounce when width, height, brightness, contrast, inversion, ASCII density style or framing changes. Output is bounded to 16–120 columns and 8–60 lines.
- **Use in Editor** inserts the converted text into the currently open artwork editor. Replacing unsaved edits requires confirmation; nothing is written by this action until the editor's own Save is pressed.
- **Save as New Artwork** creates a new `artworks/<name>.txt` under the XDG configuration root, normalizes safe filenames, suffixes duplicate names, refuses symlink escapes and leaves existing art intact. Saved files can be selected through the existing per-monitor artwork picker. Export remains a separate deliberate action.
- The new conversion modules are installed as part of `install.sh`. Historical issue records, ROADMAP.md, TASKS.md and dated CHANGELOG.md are updated without removing earlier release documents.

## Still open

- Live verification of GTK/libadwaita picker, window breakpoints, TextView font characteristics and installation on GNOME/KDE; no graphical display was available for this source build.
- Keeping the original image and conversion settings in a reusable edit recipe across app restarts is **not yet implemented**. Images remain editable while their converter window is open; only the generated plain-text artwork is saved.
- Advanced controls (gamma, dithering, sharpen, edges, ANSI color), local asset metadata/search and vetted online galleries are **future Artwork Studio stages**, not part of V87.
- Automatic assignment of exported art to a particular monitor is not claimed; use the existing artwork picker explicitly.

## Verification

- `python3 -m unittest discover -s tests -q`: conversion, alpha, padding, aspect, cropping, filename traversal, duplicate names, save failures, existing editor behavior.
- `bash tests/test_installers.sh`, `bash tests/test_session_detection.sh`, `python3 scripts/check-release-assets.py` and Python compileall checks.
- ZIP integrity verified. Rust build, runtime GTK, Wayland and two-monitor behavior are **not tested** in this environment.
