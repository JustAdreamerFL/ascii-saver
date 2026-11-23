# ASCII Saver V99 (0.99.0)

Date: 2026-11-08. Experimental cumulative source release.

## Artwork Studio: keyboard-accessible drawing and safer text changes

- Canvas accepts four arrow keys to move a **visible drawing cursor** between
  individual character cells, including after keyboard focus is given to the
  canvas. `Space` paints the selected printable ASCII glyph; `Delete` or
  `Backspace` erase the selected cell. Each effective keyboard action enters
  the same native GTK Undo history as a mouse gesture. Ordinary Text mode is
  still available for full keyboard text editing and Unicode artwork.
- Show a small contextual **Cell column, row** indicator in the existing hint
  line instead of adding another toolbar. When the cursor moves outside the
  visible scrollable area, adjustment values follow it and remain clamped.
  Mouse hover/drag can take over the highlighting naturally. GTK keeps normal
  Tab navigation and modifier-based desktop shortcuts.
- **Fix unnecessary whole-document replacement on Canvas paint.** Only the
  differing range is deleted and inserted in the Gtk.TextBuffer. A grouped
  user action remains one Undo step. Hold off Canvas refresh during intermediate
  buffer events, then refresh once with the completed text; this avoids
  resetting the keyboard cursor to a small default canvas mid-edit, and
  reduces work and disturbance to unrelated text marks.
- Pure geometry helpers for directional cursor motion and visible scrolling
  live in `artwork_canvas.py`; `artwork_canvas_view.py` handles key commands,
  cursor drawing, and viewport adjustments, while `artwork_editor.py` owns the
  existing undoable shared text buffer and hint text.
- Update the V97/V98 fake GTK test fixtures for the newly supported keyboard
  cursor and add `tests/test_v99_keyboard_canvas.py` for movement, bounds,
  painting/erasing, scroll visibility, modifier shortcuts, and partial-buffer
  edits that must not redraw the in-progress state.

## Not implemented or not verified

- No disk writes occur without the existing explicit Save, and the renderer
  and artwork file formats are unchanged. No rectangle-selection, layers or
  additional multi-cell tools were introduced.
- Actual GTK keyboard focus, arrow events, fractional-scale scrolling, canvas
  rendering and screen-reader behavior must be tested on GNOME/KDE Wayland.
- No new Rust renderer build is claimed. Artwork Studio M1 remains open.
