"""Native, self-contained text editor for a selected ASCII artwork file."""
from __future__ import annotations
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Pango, Gdk
from window_shortcuts import install_close_shortcuts
from artwork_editor_io import read_artwork, save_artwork, editor_close_message
from artwork_retouch import paint_at, paint_selection, mirror_selection, flip_selection, validate_ink
from artwork_canvas_view import AsciiCanvas
from photo_project import reference_for_artwork


class ArtworkEditor(Adw.Window):
    def __init__(self, parent, path: Path, on_finished=None, config_dir=None):
        super().__init__(transient_for=parent, title=f"Edit Artwork · {path.name}")
        install_close_shortcuts(self, Gtk, Gdk)
        self.set_default_size(850, 650)
        self.path = path
        # A preferences window can supply the exact XDG configuration root.
        # Legacy callers infer it from the current artwork location.
        self.config_dir = Path(config_dir) if config_dir is not None else (
            path.parent.parent if path.parent.name == "artworks" else path.parent)
        self.original_text = read_artwork(path)
        self._on_finished = on_finished
        self._saved_count = 0
        self._discarded_edits = False
        self._close_confirmed = False
        self._close_dialog_open = False
        self._reported_close = False
        self._canvas_commit_in_progress = False
        self._templates_window = None
        self._photo_window = None
        self._library_window = None
        # The built-in editor must not silently discard edits on Escape,
        # Cancel, or the window-manager Close action.
        self.connect("close-request", self._close_requested)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        cancel = Gtk.Button(label="Close")
        cancel.connect("clicked", lambda *_: self.close())
        header.pack_start(cancel)
        templates = Gtk.Button(label="Explore Styles")
        templates.set_tooltip_text("Start from an editable, original ASCII template")
        templates.connect("clicked", self._open_templates)
        header.pack_start(templates)
        retouch = Gtk.MenuButton(label="Retouch")
        retouch.set_tooltip_text("Paint or erase a character, mirror selected art and undo edits")
        retouch.set_popover(self._build_retouch_popover())
        # Keep the already-crowded header at its previous width. Retouch lives
        # on a compact secondary bar instead of adding a seventh header action.
        photo = Gtk.Button(label="Photo to ASCII")
        photo.set_tooltip_text("Convert an image and compare it with editable ASCII art")
        photo.connect("clicked", self._open_photo)
        header.pack_start(photo)
        self._saved_photo_reference = reference_for_artwork(self.config_dir, path)
        if self._saved_photo_reference is not None:
            reopen = Gtk.Button(label="Reopen Photo")
            reopen.set_tooltip_text("Reopen the original image and conversion settings. Export a new variant without overwriting the current art.")
            reopen.connect("clicked", self._reopen_photo)
            header.pack_start(reopen)
        save = Gtk.Button(label="Save")
        save.add_css_class("suggested-action")
        header.pack_end(save)
        library = Gtk.Button(label="My Artwork")
        library.set_tooltip_text("Browse and edit your saved ASCII artworks")
        library.connect("clicked", self._open_library)
        header.pack_start(library)
        toolbar.add_top_bar(header)
        retouch_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        retouch_bar.set_margin_start(10)
        retouch_bar.set_margin_end(10)
        retouch_bar.set_margin_top(4)
        retouch_bar.set_margin_bottom(4)
        retouch_bar.append(retouch)
        self.draw_mode = Gtk.ToggleButton(label="Draw")
        self.draw_mode.set_tooltip_text("Draw directly with mouse drag; deactivate for text editing")
        self.draw_mode.connect("toggled", self._toggle_canvas)
        self.text_mode = Gtk.ToggleButton(label="Text")
        self.text_mode.set_group(self.draw_mode)
        self.text_mode.set_active(True)
        retouch_bar.append(self.text_mode)
        retouch_bar.append(self.draw_mode)
        toolbar.add_top_bar(retouch_bar)
        # FlowBox wraps whole logical control groups on narrow windows, rather
        # than clipping the Ink/Zoom/Grid controls at mobile-like widths.
        canvas_controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        canvas_controls.set_margin_start(12)
        canvas_controls.set_margin_end(12)
        canvas_controls.set_margin_top(4)
        canvas_controls.set_margin_bottom(6)
        canvas_tools = Gtk.FlowBox()
        canvas_tools.set_selection_mode(Gtk.SelectionMode.NONE)
        canvas_tools.set_min_children_per_line(1)
        canvas_tools.set_max_children_per_line(4)
        canvas_tools.set_column_spacing(10)
        canvas_tools.set_row_spacing(4)
        canvas_tools.set_homogeneous(False)
        canvas_tools.set_hexpand(True)
        brush_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        brush_group.append(Gtk.Label(label="Brush"))
        self.canvas_ink = Gtk.Entry(text="@", max_length=1, width_chars=3)
        self.canvas_ink.set_tooltip_text("One printable ASCII character for mouse drawing")
        brush_group.append(self.canvas_ink)
        canvas_tools.insert(brush_group, -1)
        self.canvas_erase = Gtk.ToggleButton(label="Erase")
        self.canvas_erase.set_tooltip_text("Replace painted characters with spaces while dragging")
        canvas_tools.insert(self.canvas_erase, -1)
        zoom_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        zoom_group.append(Gtk.Label(label="Zoom"))
        self._canvas_zoom_levels = (75, 100, 125, 150, 200)
        self.canvas_zoom = Gtk.DropDown.new_from_strings(
            [f"{amount}%" for amount in self._canvas_zoom_levels])
        self.canvas_zoom.set_selected(1)
        self.canvas_zoom.set_tooltip_text("Magnify the character cells without changing the artwork")
        self.canvas_zoom.connect("notify::selected", self._canvas_zoom_changed)
        zoom_group.append(self.canvas_zoom)
        canvas_tools.insert(zoom_group, -1)
        self.canvas_grid = Gtk.CheckButton(label="Grid")
        self.canvas_grid.set_active(True)
        self.canvas_grid.set_tooltip_text("Show or hide the character-cell guide; never affects exported text")
        self.canvas_grid.connect("toggled", self._canvas_grid_toggled)
        canvas_tools.insert(self.canvas_grid, -1)
        # Extra workspace is display-only until ink is painted in it. Keep
        # these advanced size controls inside one compact popover.
        self.canvas_workspace = Gtk.MenuButton(label="Work area")
        self.canvas_workspace.set_tooltip_text(
            "Expand the drawing grid without inserting spaces or resizing existing artwork")
        workspace_popover = Gtk.Popover()
        workspace_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for margin in ("top", "bottom", "start", "end"):
            getattr(workspace_panel, f"set_margin_{margin}")(12)
        workspace_panel.append(Gtk.Label(label="Drawing work area", xalign=0))
        workspace_panel.append(Gtk.Label(
            label="Unpainted cells are not saved. Existing art is never cropped.",
            xalign=0, wrap=True))
        size_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        size_row.append(Gtk.Label(label="Columns"))
        self.canvas_columns = Gtk.SpinButton.new_with_range(48, 200, 1)
        self.canvas_columns.set_value(48)
        size_row.append(self.canvas_columns)
        size_row.append(Gtk.Label(label="Rows"))
        self.canvas_rows = Gtk.SpinButton.new_with_range(18, 100, 1)
        self.canvas_rows.set_value(18)
        size_row.append(self.canvas_rows)
        workspace_panel.append(size_row)
        size_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        apply_workspace = Gtk.Button(label="Apply size")
        apply_workspace.add_css_class("suggested-action")
        apply_workspace.connect("clicked", self._canvas_workspace_apply)
        size_buttons.append(apply_workspace)
        fit_workspace = Gtk.Button(label="Fit to artwork")
        fit_workspace.connect("clicked", self._canvas_workspace_fit)
        size_buttons.append(fit_workspace)
        workspace_panel.append(size_buttons)
        workspace_popover.set_child(workspace_panel)
        self.canvas_workspace.set_popover(workspace_popover)
        canvas_tools.insert(self.canvas_workspace, -1)
        canvas_controls.append(canvas_tools)
        canvas_hint = Gtk.Label(
            label="Arrows move; Space paints; Delete erases. Drag or scroll with the mouse.",
            xalign=0, hexpand=True)
        self.canvas_hint = canvas_hint
        canvas_hint.add_css_class("dim-label")
        canvas_hint.set_ellipsize(Pango.EllipsizeMode.END)
        canvas_controls.append(canvas_hint)
        self.canvas_controls = canvas_controls
        canvas_controls.set_visible(False)
        toolbar.add_top_bar(canvas_controls)
        self.ink_entry.connect("changed", self._sync_popover_ink)
        self.canvas_ink.connect("changed", self._sync_canvas_ink)
        self.save_button = save

        self.editor = Gtk.TextView(monospace=True, left_margin=18, right_margin=18,
                                   top_margin=18, bottom_margin=18)
        self.editor.set_wrap_mode(Gtk.WrapMode.NONE)
        buffer = self.editor.get_buffer()
        buffer.set_text(self.original_text)
        # GTK native undo groups brush actions without making a new file write.
        buffer.set_enable_undo(True)
        buffer.set_max_undo_levels(80)
        buffer.connect("changed", self._changed)
        buffer.connect("notify::can-undo", self._sync_retouch_history)
        buffer.connect("notify::can-redo", self._sync_retouch_history)
        scroller = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scroller.set_child(self.editor)
        self.canvas_view = AsciiCanvas(
            buffer,
            get_ink=self.canvas_ink.get_text,
            is_erasing=self.canvas_erase.get_active,
            on_commit=self._commit_canvas_stroke,
            on_error=self._canvas_error,
            on_undo=self._undo_edit,
            on_redo=self._redo_edit,
            on_position=self._canvas_position_changed,
        )
        self.editor_pages = Gtk.Stack()
        self.editor_pages.set_transition_type(Gtk.StackTransitionType.NONE)
        self.editor_pages.add_named(scroller, "text")
        self.editor_pages.add_named(self.canvas_view, "canvas")
        self.editor_pages.set_visible_child_name("text")
        toolbar.set_content(self.editor_pages)
        buffer.connect("changed", self._canvas_text_changed)
        self.toasts = Adw.ToastOverlay()
        self.toasts.set_child(toolbar)
        self.set_content(self.toasts)
        save.connect("clicked", self._save)
        self._changed()
        self._sync_retouch_history()
        # A visual editor should open as a visual editor, not a hidden text area.
        # Oversized or non-cell-width artwork gracefully remains in Text mode.
        self.draw_mode.set_active(True)

    def _sync_popover_ink(self, *_unused):
        value = self.ink_entry.get_text()
        if self.canvas_ink.get_text() != value:
            self.canvas_ink.set_text(value)

    def _sync_canvas_ink(self, *_unused):
        value = self.canvas_ink.get_text()
        if self.ink_entry.get_text() != value:
            self.ink_entry.set_text(value)

    def _canvas_position_changed(self, cell):
        help_text = "Arrows move; Space paints; Delete erases. Drag or scroll with the mouse."
        if cell is None:
            self.canvas_hint.set_text(help_text)
        else:
            col, row = cell
            self.canvas_hint.set_text(f"Cell {col + 1}, {row + 1} · {help_text}")
        self.canvas_hint.set_tooltip_text(self.canvas_hint.get_text())

    def _canvas_zoom_changed(self, _dropdown, _parameter):
        if hasattr(self, "canvas_view"):
            self.canvas_view.set_zoom(
                self._canvas_zoom_levels[self.canvas_zoom.get_selected()])

    def _canvas_grid_toggled(self, _button):
        if hasattr(self, "canvas_view"):
            self.canvas_view.set_grid_visible(self.canvas_grid.get_active())

    def _canvas_workspace_apply(self, *_unused):
        if not hasattr(self, "canvas_view"):
            return
        try:
            shape = self.canvas_view.set_workspace(
                self.canvas_columns.get_value_as_int(), self.canvas_rows.get_value_as_int())
        except ValueError as error:
            self._canvas_error(str(error))
            return
        # The actual drawing area cannot be smaller than existing artwork.
        self._sync_canvas_dimensions()
        self.canvas_workspace.get_popover().popdown()

    def _canvas_workspace_fit(self, *_unused):
        shape = self.canvas_view.fit_workspace()
        self._sync_canvas_dimensions()
        self.canvas_workspace.get_popover().popdown()

    def _sync_canvas_dimensions(self):
        shape = self.canvas_view.shape
        if shape is not None:
            self.canvas_columns.set_value(shape.cols)
            self.canvas_rows.set_value(shape.rows)

    def _toggle_canvas(self, button):
        if button.get_active():
            if not self.canvas_view.refresh():
                button.set_active(False)
                return
            self.editor_pages.set_visible_child_name("canvas")
            self.canvas_controls.set_visible(True)
            self._sync_canvas_dimensions()
            self.canvas_view.canvas.grab_focus()
        else:
            self.canvas_view.cancel_stroke()
            self._canvas_position_changed(None)
            self.editor_pages.set_visible_child_name("text")
            self.canvas_controls.set_visible(False)
            self.editor.grab_focus()

    def _canvas_error(self, message):
        self.toasts.add_toast(Adw.Toast.new(message))

    def _canvas_text_changed(self, *_unused):
        # Gtk.TextBuffer emits changed on both delete and insert. Do not draw
        # the incomplete buffer in the middle of a grouped canvas edit.
        if self._canvas_commit_in_progress:
            return
        if self.draw_mode.get_active():
            if not self.canvas_view.refresh():
                self.draw_mode.set_active(False)
            else:
                self._sync_canvas_dimensions()

    def _commit_canvas_stroke(self, updated):
        """Commit only the changed text span as one native GTK Undo step.

        This preserves unrelated text marks and prevents a transient empty
        buffer from resetting Canvas navigation during multi-cell painting.
        """
        buf = self.editor.get_buffer()
        original = self._text()
        if updated == original:
            return
        prefix = 0
        while (prefix < len(original) and prefix < len(updated)
               and original[prefix] == updated[prefix]):
            prefix += 1
        suffix = 0
        while (suffix < len(original) - prefix and suffix < len(updated) - prefix
               and original[len(original) - 1 - suffix] == updated[len(updated) - 1 - suffix]):
            suffix += 1
        old_end = len(original) - suffix
        new_end = len(updated) - suffix
        self._canvas_commit_in_progress = True
        buf.begin_user_action()
        try:
            if old_end > prefix:
                buf.delete(buf.get_iter_at_offset(prefix), buf.get_iter_at_offset(old_end))
            if new_end > prefix:
                buf.insert(buf.get_iter_at_offset(prefix), updated[prefix:new_end])
        finally:
            buf.end_user_action()
            self._canvas_commit_in_progress = False
        self._canvas_text_changed()

    def _build_retouch_popover(self):
        popover = Gtk.Popover()
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        panel.set_margin_top(14)
        panel.set_margin_bottom(14)
        panel.set_margin_start(14)
        panel.set_margin_end(14)
        heading = Gtk.Label(label="Retouch artwork", xalign=0)
        heading.add_css_class("heading")
        panel.append(heading)
        explanation = Gtk.Label(
            label="Place the caret on a character, then Paint or Erase. "
                  "Select some ASCII lines to mirror or flip them.",
            xalign=0, wrap=True)
        explanation.set_max_width_chars(43)
        explanation.add_css_class("dim-label")
        panel.append(explanation)
        ink_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ink_row.append(Gtk.Label(label="Ink"))
        self.ink_entry = Gtk.Entry(text="@", max_length=1, width_chars=3)
        self.ink_entry.set_tooltip_text("One printable ASCII character")
        ink_row.append(self.ink_entry)
        paint = Gtk.Button(label="Paint at Caret")
        paint.add_css_class("suggested-action")
        paint.connect("clicked", self._paint_ink)
        ink_row.append(paint)
        erase = Gtk.Button(label="Erase")
        erase.connect("clicked", self._erase_ink)
        ink_row.append(erase)
        panel.append(ink_row)

        swatches = Gtk.FlowBox()
        swatches.set_selection_mode(Gtk.SelectionMode.NONE)
        swatches.set_max_children_per_line(10)
        swatches.set_min_children_per_line(5)
        swatches.set_column_spacing(4)
        swatches.set_row_spacing(4)
        for char in '@#*+=:-./\\|':
            button = Gtk.Button(label=char)
            button.set_tooltip_text(f"Use {char} as ink")
            button.connect("clicked", lambda _button, glyph=char: self.ink_entry.set_text(glyph))
            swatches.insert(button, -1)
        panel.append(swatches)

        selection_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mirror = Gtk.Button(label="Mirror Selection")
        mirror.set_tooltip_text("Reverse selected lines, including slash and bracket direction")
        mirror.connect("clicked", lambda *_: self._transform_selection(mirror_selection))
        selection_actions.append(mirror)
        flip = Gtk.Button(label="Flip Selection")
        flip.set_tooltip_text("Reverse the order of selected lines")
        flip.connect("clicked", lambda *_: self._transform_selection(flip_selection))
        selection_actions.append(flip)
        panel.append(selection_actions)

        history = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.retouch_undo = Gtk.Button(label="Undo")
        self.retouch_undo.connect("clicked", self._undo_edit)
        self.retouch_redo = Gtk.Button(label="Redo")
        self.retouch_redo.connect("clicked", self._redo_edit)
        history.append(self.retouch_undo)
        history.append(self.retouch_redo)
        panel.append(history)
        popover.set_child(panel)
        return popover

    def _sync_retouch_history(self, *_unused):
        buf = self.editor.get_buffer()
        self.retouch_undo.set_sensitive(buf.get_can_undo())
        self.retouch_redo.set_sensitive(buf.get_can_redo())

    def _undo_edit(self, *_unused):
        buf = self.editor.get_buffer()
        if buf.get_can_undo():
            buf.undo()
        self._restore_editing_focus()

    def _redo_edit(self, *_unused):
        buf = self.editor.get_buffer()
        if buf.get_can_redo():
            buf.redo()
        self._restore_editing_focus()

    def _restore_editing_focus(self):
        if self.draw_mode.get_active():
            self.canvas_view.canvas.grab_focus()
        else:
            self.editor.grab_focus()

    def _paint_ink(self, *_unused):
        self._paint_cell(erase=False)

    def _erase_ink(self, *_unused):
        self._paint_cell(erase=True)

    def _paint_cell(self, *, erase: bool):
        buf = self.editor.get_buffer()
        if buf.get_has_selection():
            selected, start, end = buf.get_selection_bounds()
            if selected:
                original = buf.get_text(start, end, False)
                try:
                    updated = paint_selection(original, self.ink_entry.get_text(), erase=erase)
                except ValueError as error:
                    self.toasts.add_toast(Adw.Toast.new(str(error)))
                    return
                if updated != original:
                    start_offset = start.get_offset()
                    buf.begin_user_action()
                    try:
                        buf.delete(start, end)
                        buf.insert(buf.get_iter_at_offset(start_offset), updated)
                    finally:
                        buf.end_user_action()
                    buf.select_range(buf.get_iter_at_offset(start_offset + len(updated)),
                                     buf.get_iter_at_offset(start_offset))
                self.editor.grab_focus()
                return
        offset = buf.get_iter_at_mark(buf.get_insert()).get_offset()
        try:
            glyph = ' ' if erase else validate_ink(self.ink_entry.get_text())
            old = self._text()
            updated, next_offset = paint_at(old, offset, glyph, erase=erase)
        except ValueError as error:
            self.toasts.add_toast(Adw.Toast.new(str(error)))
            return
        if updated == old:
            self.editor.grab_focus()
            return
        # Single-cell changes rather than set_text(): every click is undoable.
        buf.begin_user_action()
        try:
            if offset < len(old) and old[offset] not in '\r\n':
                buf.delete(buf.get_iter_at_offset(offset), buf.get_iter_at_offset(offset + 1))
            buf.insert(buf.get_iter_at_offset(offset), glyph)
        finally:
            buf.end_user_action()
        buf.place_cursor(buf.get_iter_at_offset(next_offset))
        self.editor.grab_focus()

    def _transform_selection(self, operation):
        buf = self.editor.get_buffer()
        if not buf.get_has_selection():
            self.toasts.add_toast(Adw.Toast.new("Select artwork text first."))
            return
        has_range, start, end = buf.get_selection_bounds()
        if not has_range:
            return
        original = buf.get_text(start, end, False)
        try:
            transformed = operation(original)
        except ValueError as error:
            self.toasts.add_toast(Adw.Toast.new(str(error)))
            return
        if transformed == original:
            return
        start_offset = start.get_offset()
        buf.begin_user_action()
        try:
            buf.delete(start, end)
            buf.insert(buf.get_iter_at_offset(start_offset), transformed)
        finally:
            buf.end_user_action()
        buf.select_range(buf.get_iter_at_offset(start_offset + len(transformed)),
                         buf.get_iter_at_offset(start_offset))
        self.editor.grab_focus()

    def _open_library(self, *_unused):
        from artwork_library_view import ArtworkLibraryWindow
        if self._library_window is not None:
            self._library_window.present()
            return
        window = ArtworkLibraryWindow(self, self.config_dir)
        self._library_window = window
        window.connect("close-request", self._library_closed)
        window.present()

    def _library_closed(self, *_unused):
        self._library_window = None
        return False

    def _open_photo(self, *_unused):
        from photo_ascii_view import PhotoAsciiWindow
        if self._photo_window is not None:
            self._photo_window.present()
            return
        window = PhotoAsciiWindow(self, self.config_dir, self._use_photo)
        self._photo_window = window
        window.connect("close-request", self._photo_closed)
        window.present()

    def _reopen_photo(self, *_unused):
        # An existing conversion window may contain unsaved adjustments; do
        # not silently reset them when this button is clicked twice.
        if self._photo_window is not None:
            self._photo_window.present()
            return
        from photo_ascii_view import PhotoAsciiWindow
        window = PhotoAsciiWindow(self, self.config_dir, self._use_photo,
                                  saved_reference=self._saved_photo_reference)
        self._photo_window = window
        window.connect("close-request", self._photo_closed)
        window.present()

    def _photo_closed(self, *_unused):
        self._photo_window = None
        return False

    def _use_photo(self, artwork: str, window):
        # Conversion is never an implicit write. Respect unsaved edits exactly
        # as the template picker does.
        from types import SimpleNamespace
        template = SimpleNamespace(artwork=artwork)
        if self._text() != self.original_text:
            self._confirm_photo_replace(template, window)
            return
        self._replace_with_template(template, window)

    def _confirm_photo_replace(self, template, window):
        heading = "Replace unsaved edits?"
        detail = "The converted photo will replace your current text. The original image and artwork file remain unchanged until Save."
        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog.new(heading, detail)
            modern = True
        else:
            dialog = Adw.MessageDialog.new(self, heading, detail)
            modern = False
        dialog.add_response("keep", "Keep editing")
        dialog.add_response("replace", "Use Converted Photo")
        dialog.set_default_response("keep")
        dialog.set_close_response("keep")
        dialog.set_response_appearance("replace", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", lambda _dialog, response: (
            self._replace_with_template(template, window) if response == "replace" else None))
        if modern:
            dialog.present(self)
        else:
            dialog.present()

    def _open_templates(self, *_unused):
        from artwork_templates_view import ArtworkTemplatesWindow
        if self._templates_window is not None:
            self._templates_window.present()
            return
        picker = ArtworkTemplatesWindow(self, self._use_template)
        self._templates_window = picker
        picker.connect("close-request", self._templates_closed)
        picker.present()

    def _templates_closed(self, *_unused):
        self._templates_window = None
        return False

    def _use_template(self, template, picker):
        # Replacing a dirty buffer must not silently destroy work; template
        # insertion is local until the existing Save button writes to disk.
        if self._text() != self.original_text:
            self._confirm_template_replace(template, picker)
            return
        self._replace_with_template(template, picker)

    def _replace_with_template(self, template, picker):
        self.editor.get_buffer().set_text(template.artwork)
        picker.close()
        self.editor.grab_focus()

    def _confirm_template_replace(self, template, picker):
        heading = "Replace unsaved edits?"
        detail = "The chosen template will replace the current text. Your file stays unchanged until Save."
        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog.new(heading, detail)
            modern = True
        else:
            dialog = Adw.MessageDialog.new(self, heading, detail)
            modern = False
        dialog.add_response("keep", "Keep editing")
        dialog.add_response("replace", "Use Template")
        dialog.set_default_response("keep")
        dialog.set_close_response("keep")
        dialog.set_response_appearance("replace", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", lambda _dialog, response: (
            self._replace_with_template(template, picker) if response == "replace" else None))
        if modern:
            dialog.present(self)
        else:
            dialog.present()

    def _text(self):
        buf = self.editor.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)

    def _changed(self, *_unused):
        self.save_button.set_sensitive(self._text() != self.original_text)

    def _save(self, *_unused):
        content = self._text()
        try:
            save_artwork(self.path, content)
        except OSError as error:
            self.toasts.add_toast(Adw.Toast.new(f"Could not save artwork: {error}"))
            return
        self.original_text = content
        self._saved_count += 1
        self._changed()
        self.toasts.add_toast(Adw.Toast.new("Artwork saved."))

    def _close_requested(self, *_unused):
        if self._text() != self.original_text and not self._close_confirmed:
            if not self._close_dialog_open:
                self._confirm_discard()
            return True
        if not self._reported_close:
            if hasattr(self, "_templates_window") and self._templates_window is not None:
                self._templates_window.close()
            if hasattr(self, "_photo_window") and self._photo_window is not None:
                self._photo_window.close()
            self._reported_close = True
            message = editor_close_message(self._saved_count, self._discarded_edits)
            if self._on_finished is not None:
                self._on_finished(message)
        return False

    def _confirm_discard(self):
        self._close_dialog_open = True
        heading = "Discard unsaved edits?"
        detail = "Changes that were not saved to the artwork file will be lost."
        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog.new(heading, detail)
            dialog.add_response("keep", "Keep editing")
            dialog.add_response("discard", "Discard")
            dialog.set_default_response("keep")
            dialog.set_close_response("keep")
            dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response", self._discard_response)
            dialog.present(self)
        else:
            # Older libadwaita releases have MessageDialog instead.
            dialog = Adw.MessageDialog.new(self, heading, detail)
            dialog.add_response("keep", "Keep editing")
            dialog.add_response("discard", "Discard")
            dialog.set_default_response("keep")
            dialog.set_close_response("keep")
            dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response", self._discard_response)
            dialog.present()

    def _discard_response(self, _dialog, response):
        self._close_dialog_open = False
        if response == "discard":
            self._discarded_edits = True
            self._close_confirmed = True
            self.close()
