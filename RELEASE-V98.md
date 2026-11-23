# ASCII Saver V98 (0.98.0)

Date: 2026-11-08. Experimental cumulative source release.

## Canvas viewport, responsive controls and keyboard navigation

V97 introduced a printable-ASCII drawing surface backed by the native
Gtk.TextBuffer. V98 improves its visual control without introducing a new
asset format or any additional drawing tool that cannot be verified locally.

- The Canvas toolbar now adapts to narrow windows using a FlowBox of complete
  control groups. Brush, Erase, Zoom and Grid stay available when the editor
  narrows, with a brief scroll and keyboard tip below.
- Zoom choices: 75%, 100% (default), 125%, 150%, 200%. A common Pango font
  description controls both glyph drawing and cell measurement. GTK pointer
  events and Pango extents use logical widget coordinates, so no second
  monitor-scale-factor multiplication is applied. The canvas remains in a
  ScrolledWindow and attempts to preserve the top-left visible character on
  zoom. The scroll request is clamped and outdated requests are ignored.
- Grid visibility is cosmetic. Hiding the grid never changes source text;
  zoom changes only the rendered glyph and cell sizes.
- Canvas can take keyboard focus. Ctrl+Z, Ctrl+Shift+Z or Ctrl+Y use native
  TextBuffer Undo/Redo and restore focus to the active editor mode. A gesture
  in progress is cancelled on zoom or on returning to Text mode.

## Source changes

- `artwork_canvas.py`: pure pointer-to-cell and zoom-scroll calculations.
- `artwork_canvas_view.py`: consistent font measurement, zoom, grid, focus
  and shortcuts, guarded deferred scroll restoration, stroke cancellation.
- `artwork_editor.py`: responsive tool grouping and mode-aware Undo/Redo.
- `tests/test_v98_canvas_viewport.py`: pure geometry and simulated behavior
  tests without requiring GTK or a Wayland session.
- `tests/test_v97_mouse_canvas.py`: fake canvas updated to accept focus and
  its version check tests the V97 lower bound, not an exact release number.
- `VERSION`, `build_info.py`, `README.md`, `TASKS.md`, `ROADMAP.md`,
  `MASTER-BACKLOG.md`, `CHANGELOG.md`: version and status tracking.

## Validation scope

Source and headless geometry/control tests exercise the non-destructive
behavior. Installer, session detection and ZIP checks are independent.
The container cannot validate a live GTK/VTE session, actual 125%/150% display
scaling, pointer capture/focus propagation or GTK viewport allocation timing.
GNOME/KDE Wayland checks remain required. The Rust renderer is unchanged
and is not claimed to have been rebuilt. Artwork Studio M1 remains open.
