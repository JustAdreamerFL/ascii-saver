# ASCII Saver V97 (0.97.0)

Date: 2026-11-08. Experimental cumulative source release.

## Mouse Canvas: artwork retouch without caret placement

The Artwork Editor offers a **Draw on Canvas** toggle in its secondary toolbar.
The new scrollable character-cell surface shows the current art, a subtle grid
and a mouse-hover outline. Choose printable ASCII ink (one character) or Erase
and drag with the left mouse button; continuous/rapid mouse motion is
interpolated so lines do not have gaps. A stroke previews during dragging and
is committed only on pointer release. Switch to Text mode to edit by keyboard.

Both modes edit the **same** in-memory GTK text buffer. A completed stroke is
exactly one user-action for Undo; redo, explicit Save, and unsaved-discard
confirmation remain owned by the existing editor. Erase does not grow text,
while Paint can create new rows and pad spaces to the chosen character cell.
There is no new artwork file format, network dependency or automatic export.

The mouse canvas deliberately rejects tabs, control sequences, wide Unicode
and artworks exceeding 200 columns / 100 rows. The original text remains
unchanged and still editable in Text mode. Rectangular selection, layers
and special multi-cell brushes are not included.

## Files changed

- `artwork_canvas.py`: bounded, pure deterministic grid/stroke engine.
- `artwork_canvas_view.py`: GTK4/PangoCairo scrollable grid, pointer drag and hover.
- `artwork_editor.py`: canvas/text switch, brush/erase controls and shared undoable buffer.
- `tests/test_v97_mouse_canvas.py`: pure-engine and direct buffer regressions.
- `install.sh`, `VERSION`, `build_info.py`, `TASKS.md`, `ROADMAP.md`,
  `MASTER-BACKLOG.md`, `CHANGELOG.md`, `README.md`: packaging and status.

## Validation and constraints

Python regression suite and installer/desktop recognition checks are run in
the release build. The container lacks a live GTK/VTE desktop, so gesture
capture, fractional scaling, pointer precision, scrolling, viewport sizing,
real keyboard Undo and GNOME/KDE Wayland rendering are **not yet validated**.
Rust Cargo rebuild was not run. Status does not imply a production-ready
release or closure of Artwork Studio M1.
