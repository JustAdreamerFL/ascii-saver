"""Native mouse canvas for printable-ASCII artwork, backed by the text editor.

The canvas never writes files. Its commits go through a single Gtk.TextBuffer
user-action so dragging is one Undo step and Save stays explicit.
"""
from __future__ import annotations
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango, PangoCairo, Gdk, GLib
from artwork_canvas import (CanvasShape, canvas_shape, validate_workspace,
                            visible_cell_range, line_cells, paint_stroke, canvas_cell_at,
                            zoom_scroll_offset, ZOOM_LEVELS, move_canvas_cursor,
                            canvas_reveal_offset, KEYBOARD_DIRECTIONS)
from artwork_retouch import validate_ink


class AsciiCanvas(Gtk.ScrolledWindow):
    PAD = 16

    def __init__(self, buffer, *, get_ink, is_erasing, on_commit, on_error,
                 on_undo, on_redo, on_position=None):
        super().__init__(hexpand=True, vexpand=True)
        self.buffer = buffer
        self.get_ink = get_ink
        self.is_erasing = is_erasing
        self.on_commit = on_commit
        self.on_error = on_error
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_position = on_position
        self.zoom = 100
        self.show_grid = True
        self._zoom_serial = 0
        self._font_description = Pango.FontDescription("Monospace 13")
        self.cell_width = 10
        self.cell_height = 20
        self.shape = None
        self.workspace = CanvasShape(48, 18)
        self.hover = None
        self.keyboard_cell = (0, 0)
        self.keyboard_active = False
        self._stroke = set()
        self._stroke_origin = None
        self._previous_cell = None
        self._painting = False
        self._click_pending = False
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_draw_func(self._draw)
        self.canvas.set_focusable(True)
        keys = Gtk.EventControllerKey()
        keys.connect('key-pressed', self._key_pressed)
        self.canvas.add_controller(keys)
        self.canvas.set_tooltip_text('Drag with the mouse, or use arrow keys to move, Space to paint and Delete to erase. Switch to Text for typing.')
        self.set_child(self.canvas)
        drag = Gtk.GestureDrag()
        drag.set_button(1)
        drag.connect('drag-begin', self._drag_begin)
        drag.connect('drag-update', self._drag_update)
        drag.connect('drag-end', self._drag_end)
        self.canvas.add_controller(drag)
        click = Gtk.GestureClick()
        click.set_button(1)
        click.connect('pressed', self._click_pressed)
        click.connect('released', self._click_released)
        self.canvas.add_controller(click)
        motion = Gtk.EventControllerMotion()
        motion.connect('motion', self._motion)
        motion.connect('leave', self._leave)
        self.canvas.add_controller(motion)

    def _read_text(self):
        return self.buffer.get_text(self.buffer.get_start_iter(),
                                    self.buffer.get_end_iter(), False)

    def cancel_stroke(self):
        """Never commit an unfinished stroke when leaving Canvas mode."""
        self._stroke.clear()
        self._stroke_origin = None
        self._previous_cell = None
        self._painting = False
        self.canvas.queue_draw()

    def set_workspace(self, cols: int, rows: int):
        """Resize only empty drawing space, never the saved ASCII text."""
        requested = validate_workspace(CanvasShape(cols, rows))
        current = canvas_shape(self._read_text(), requested)
        self.cancel_stroke()
        self.workspace = requested
        self.refresh()
        return current

    def fit_workspace(self):
        """Return to artwork dimensions (at least 48x18), no text mutation."""
        return self.set_workspace(48, 18)

    def set_grid_visible(self, visible: bool):
        self.show_grid = bool(visible)
        self.canvas.queue_draw()

    def set_zoom(self, zoom: int):
        """Change font and hit-test geometry, keeping the visible cell anchored."""
        if zoom not in ZOOM_LEVELS:
            raise ValueError('Unsupported canvas zoom level.')
        if zoom == self.zoom:
            return
        h_adjust = self.get_hadjustment()
        v_adjust = self.get_vadjustment()
        old_w, old_h = self.cell_width, self.cell_height
        old_x = h_adjust.get_value()
        old_y = v_adjust.get_value()
        self.cancel_stroke()
        self.zoom = zoom
        if not self.refresh():
            return
        target_x = zoom_scroll_offset(old_x, old_w, self.cell_width, padding=self.PAD)
        target_y = zoom_scroll_offset(old_y, old_h, self.cell_height, padding=self.PAD)
        self._zoom_serial += 1
        serial = self._zoom_serial
        # The content allocation must update GTK adjustments first.
        GLib.idle_add(self._restore_scroll_after_zoom, serial, target_x, target_y)

    def _restore_scroll_after_zoom(self, serial, target_x, target_y):
        if serial != self._zoom_serial:
            return False
        for adjustment, target in ((self.get_hadjustment(), target_x),
                                   (self.get_vadjustment(), target_y)):
            upper = max(adjustment.get_lower(),
                        adjustment.get_upper() - adjustment.get_page_size())
            adjustment.set_value(min(upper, max(adjustment.get_lower(), target)))
        return False

    def _key_pressed(self, _controller, keyval, _keycode, state):
        key = (Gdk.keyval_name(keyval) or '').lower()
        if key.startswith('kp_') and key[3:] in KEYBOARD_DIRECTIONS:
            key = key[3:]
        if key == 'kp_space':
            key = 'space'
        if state & Gdk.ModifierType.CONTROL_MASK:
            if key == 'z':
                if state & Gdk.ModifierType.SHIFT_MASK:
                    self.on_redo()
                else:
                    self.on_undo()
                return True
            if key == 'y':
                self.on_redo()
                return True
            return False
        # Preserve GTK's normal focus traversal and desktop key bindings.
        alt_mask = getattr(Gdk.ModifierType, 'ALT_MASK',
                           getattr(Gdk.ModifierType, 'MOD1_MASK', 0))
        super_mask = getattr(Gdk.ModifierType, 'SUPER_MASK', 0)
        if state & (alt_mask | super_mask | Gdk.ModifierType.SHIFT_MASK):
            return False
        if self.shape is None:
            return False
        if key in KEYBOARD_DIRECTIONS:
            self.keyboard_cell = move_canvas_cursor(self.keyboard_cell, key, self.shape)
            # Do not let an earlier deferred zoom restore override navigation.
            self._zoom_serial += 1
            self.keyboard_active = True
            self._notify_cell(self.keyboard_cell)
            self._reveal_keyboard_cell()
            self.canvas.queue_draw()
            return True
        if key in ('space', 'backspace', 'delete', 'kp_delete'):
            self.keyboard_active = True
            self._notify_cell(self.keyboard_cell)
            self._paint_keyboard_cell(erase=key != 'space')
            return True
        if key == 'escape' and self._painting:
            self.cancel_stroke()
            return True
        return False

    def _notify_cell(self, cell):
        if self.on_position is not None:
            self.on_position(cell)

    def _paint_keyboard_cell(self, *, erase):
        """Keyboard editing is one undoable commit on the shared buffer."""
        if self._painting or self.shape is None:
            return
        try:
            text = self._read_text()
            updated = paint_stroke(text, (self.keyboard_cell,), self.get_ink(),
                                   erase=erase, workspace=self.shape)
        except ValueError as error:
            self.on_error(str(error))
            return
        if updated != text:
            self.on_commit(updated)
        self._reveal_keyboard_cell()
        self.canvas.queue_draw()

    def _reveal_keyboard_cell(self):
        col, row = self.keyboard_cell
        for adjustment, index, extent in (
                (self.get_hadjustment(), col, self.cell_width),
                (self.get_vadjustment(), row, self.cell_height)):
            page_size = adjustment.get_page_size()
            if page_size <= 0:
                continue
            desired = canvas_reveal_offset(adjustment.get_value(), page_size,
                                           self.PAD + index * extent, extent)
            lower = adjustment.get_lower()
            maximum = max(lower, adjustment.get_upper() - page_size)
            adjustment.set_value(min(maximum, max(lower, desired)))

    def refresh(self):
        """Call on entry to Canvas mode and whenever the buffer is edited."""
        text = self._read_text()
        try:
            self.shape = canvas_shape(text, self.workspace)
        except ValueError as error:
            self.shape = None
            self.on_error(str(error))
            return False
        # Keep the keyboard drawing cursor valid after undo/redo or text edits.
        col, row = self.keyboard_cell
        self.keyboard_cell = (min(max(0, col), self.shape.cols - 1),
                              min(max(0, row), self.shape.rows - 1))
        layout = self.canvas.create_pango_layout('M')
        self._font_description = Pango.FontDescription("Monospace")
        self._font_description.set_size(round(13 * Pango.SCALE * self.zoom / 100))
        layout.set_font_description(self._font_description)
        width, height = layout.get_pixel_size()
        self.cell_width = max(8, width)
        self.cell_height = max(16, height + 4)
        self.canvas.set_content_width(self.shape.cols * self.cell_width + 2 * self.PAD)
        self.canvas.set_content_height(self.shape.rows * self.cell_height + 2 * self.PAD)
        self.canvas.queue_draw()
        return True

    def _cell_at(self, x, y):
        if self.shape is None:
            return None
        return canvas_cell_at(x, y, self.shape, self.cell_width,
                              self.cell_height, padding=self.PAD)

    def _motion(self, _controller, x, y):
        cell = self._cell_at(x, y)
        if cell != self.hover or self.keyboard_active:
            self.keyboard_active = False
            self.hover = cell
            self._notify_cell(cell)
            self.canvas.queue_draw()

    def _leave(self, *_unused):
        self.hover = None
        if not self.keyboard_active:
            self._notify_cell(None)
        self.canvas.queue_draw()

    def _click_pressed(self, _gesture, presses, x, y):
        self._click_pending = presses == 1 and self._cell_at(x, y) is not None

    def _click_released(self, _gesture, presses, x, y):
        if not self._click_pending or self._painting:
            return
        self._click_pending = False
        cell = self._cell_at(x, y)
        if cell is None:
            return
        try:
            text = self._read_text()
            updated = paint_stroke(text, (cell,), self.get_ink(),
                                   erase=self.is_erasing(), workspace=self.shape)
        except ValueError as error:
            self.on_error(str(error))
            return
        if text != updated:
            self.on_commit(updated)
        self.keyboard_cell = cell
        self.canvas.queue_draw()

    def _drag_begin(self, _gesture, x, y):
        self._click_pending = False
        cell = self._cell_at(x, y)
        if cell is not None:
            self.canvas.grab_focus()
            self.keyboard_active = False
            self.keyboard_cell = cell
            self._notify_cell(cell)
        self._stroke_origin = (x, y)
        self._previous_cell = cell
        self._stroke = {cell} if cell is not None else set()
        self._painting = cell is not None
        if not self._painting:
            return
        try:
            if not self.is_erasing():
                validate_ink(self.get_ink())
        except ValueError as error:
            self._painting = False
            self._stroke.clear()
            self.on_error(str(error))
        self.canvas.queue_draw()

    def _drag_update(self, _gesture, dx, dy):
        if not self._painting or self._stroke_origin is None:
            return
        x0, y0 = self._stroke_origin
        cell = self._cell_at(x0 + dx, y0 + dy)
        if cell is not None:
            self.keyboard_cell = cell
            if self._previous_cell is None:
                self._stroke.add(cell)
            else:
                self._stroke.update(line_cells(*self._previous_cell, *cell))
        self._previous_cell = cell
        self.canvas.queue_draw()

    def _drag_end(self, gesture, dx, dy):
        self._drag_update(gesture, dx, dy)
        if self._painting and self._stroke:
            try:
                updated = paint_stroke(self._read_text(), self._stroke,
                                       self.get_ink(), erase=self.is_erasing(),
                                       workspace=self.shape)
                if updated != self._read_text():
                    self.on_commit(updated)
            except ValueError as error:
                self.on_error(str(error))
        self._stroke.clear()
        self._stroke_origin = None
        self._previous_cell = None
        self._painting = False
        self.canvas.queue_draw()

    def _draw(self, area, cr, width, height):
        dark = Adw.StyleManager.get_default().get_dark()
        if dark:
            background, grid, ink, highlight = ((0.12, 0.13, 0.14), (0.19, 0.20, 0.22),
                                                (0.93, 0.93, 0.94), (0.27, 0.42, 0.55))
        else:
            background, grid, ink, highlight = ((0.98, 0.98, 0.97), (0.92, 0.92, 0.90),
                                                (0.12, 0.14, 0.16), (0.76, 0.86, 0.96))
        cr.set_source_rgb(*background)
        cr.paint()
        if self.shape is None:
            return
        hadj, vadj = self.get_hadjustment(), self.get_vadjustment()
        first_col, last_col = visible_cell_range(hadj.get_value(), hadj.get_page_size(),
                                                 self.cell_width, self.shape.cols, padding=self.PAD)
        first_row, last_row = visible_cell_range(vadj.get_value(), vadj.get_page_size(),
                                                 self.cell_height, self.shape.rows, padding=self.PAD)
        if first_col >= last_col or first_row >= last_row:
            return
        left = self.PAD + first_col * self.cell_width
        right = self.PAD + last_col * self.cell_width
        top = self.PAD + first_row * self.cell_height
        bottom = self.PAD + last_row * self.cell_height
        if self.show_grid:
            cr.set_source_rgb(*grid)
            cr.set_line_width(0.6)
            for col in range(first_col, last_col + 1):
                x = self.PAD + col * self.cell_width + .5
                cr.move_to(x, top)
                cr.line_to(x, bottom)
            for row in range(first_row, last_row + 1):
                y = self.PAD + row * self.cell_height + .5
                cr.move_to(left, y)
                cr.line_to(right, y)
            cr.stroke()
        # Layout only visible text. The character advances are fixed-width and
        # the substring is placed at its original column, preserving alignment.
        lines = self._read_text().split('\n')
        layout = area.create_pango_layout('')
        layout.set_font_description(self._font_description)
        cr.set_source_rgb(*ink)
        for row in range(first_row, min(last_row, len(lines))):
            visible = lines[row][first_col:last_col]
            if visible:
                layout.set_text(visible)
                cr.move_to(left, self.PAD + row * self.cell_height + 2)
                PangoCairo.show_layout(cr, layout)
        if self._painting and self._stroke:
            visible_stroke = [(col, row) for col, row in self._stroke
                              if first_col <= col < last_col and first_row <= row < last_row]
            cr.set_source_rgb(*highlight)
            for col, row in visible_stroke:
                cr.rectangle(self.PAD + col * self.cell_width,
                             self.PAD + row * self.cell_height,
                             self.cell_width, self.cell_height)
            cr.fill()
            try:
                glyph = ' ' if self.is_erasing() else validate_ink(self.get_ink())
                layout.set_text(glyph)
                cr.set_source_rgb(*ink)
                for col, row in visible_stroke:
                    cr.move_to(self.PAD + col * self.cell_width,
                               self.PAD + row * self.cell_height + 2)
                    PangoCairo.show_layout(cr, layout)
            except ValueError:
                pass
        elif self.hover is not None or self.keyboard_active:
            col, row = self.keyboard_cell if self.keyboard_active else self.hover
            if first_col <= col < last_col and first_row <= row < last_row:
                cr.set_source_rgba(0.30, 0.50, 0.75, .65)
                cr.set_line_width(1.5)
                cr.rectangle(self.PAD + col * self.cell_width + .6,
                             self.PAD + row * self.cell_height + .6,
                             self.cell_width - 1.2, self.cell_height - 1.2)
                cr.stroke()
