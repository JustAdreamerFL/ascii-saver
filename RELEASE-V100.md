# ASCII Saver V100 (0.100.0)

Date: 2026-11-08. Experimental cumulative source release.

## Artwork Studio: expandable work area and bounded viewport redraws

- **Work area** is a compact secondary popover in Draw on Canvas. Choose 48-200
  columns and 18-100 rows, press **Apply size**, or use **Fit to artwork**.
  The visible grid can be larger than its existing content; it never writes
  trailing spaces or empty rows just to reserve room. Fitting cannot crop
  existing artwork. Painting into the new region extends only the touched
  text, and erasing untouched empty cells remains a no-op. All real edits
  still use the shared GtkTextBuffer and the explicit Save/Discard workflow.
- The pure `artwork_canvas.py` model validates work-area dimensions and lets
  brush/eraser actions target the larger virtual shape without changing the
  previous default for callers that do not request expansion. Printable ASCII
  and the 200x100 safety limits are unchanged. Unicode artwork stays in Text.
- **Viewport rendering** in `artwork_canvas_view.py` uses the visible scroll
  ranges, with one guard cell, to draw only the visible grid lines, text
  substrings and brush preview. Large art no longer needs a Pango text
  layout for each off-screen row on every mouse-motion redraw. Character-cell
  mapping uses the same logical coordinates and current zoom as V98/V99.
- The popover is intentionally progressive disclosure, not a fifth permanent
  numeric toolbar. Work-area changes affect the editor view only, not the
  photo project file, plain `.txt` renderer asset, cache or other windows.

## Verification

- Added `tests/test_v100_work_area.py` with GTK-free checks for expanded
  painting, no-op erasing, shrink safety, invalid dimensions, Unicode
  preservation, viewport clipping and real source-wired work-area handlers.
- Full Python regression suite: **550 passed, 1 skipped** (551 total).
  `bash tests/test_installers.sh`, `bash tests/test_session_detection.sh` and
  `python3 -m compileall -q .` passed. Cumulative archive integrity is
  checked after packaging.
- Still **not verified**: real GTK drawing and scrolling on GNOME/KDE Wayland,
  Pango/HiDPI alignment, popover focus and resize behavior, or the Rust
  renderer build. No external online refresh is claimed in V100.

## Remaining work

- Real desktop validation of Draw on Canvas, keyboard focus, mouse gestures,
  Undo/Redo and fractional scaling is required before declaring the milestone
  complete. Rectangle selection, layers and extra brushes are intentionally
  deferred until the existing experience is verified.
