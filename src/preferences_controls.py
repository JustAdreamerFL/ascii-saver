"""Construction of editable GTK/libadwaita preference controls.

Their placement in HIG groups and pages is handled by preferences_pages.py.
"""
from __future__ import annotations
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib, Pango, Gio
from pathlib import Path
from adwaita_ui import make_group, adaptive_action_row
from artwork_library import import_artwork_file
from preferences_defaults import default_for, install_numeric_reset
from helpers import load_config, DEFAULT_CONFIG
from palette_editor_model import MAX_COLORS, add_color, remove_color, reset_colors
import ctl

class PreferenceControlsMixin:
    def _make_common_widgets(self):
        general = self._page_boxes["general"]
        appearance = self._page_boxes["appearance"]
        displays = self._page_boxes["displays"]
        animations = self._page_boxes["animations"]
        preview_page = self._page_boxes["preview"]
        # Real Adw.PreferencesPage/PreferencesGroup rows replace the legacy
        # Gtk.Frame + two-column Gtk.Grid settings forms. libadwaita handles
        # spacing, column widths and adaptive margins.
        section_groups = {}
        for name, title, description in (
            ("general", "Activation", None),
            ("appearance", "Artwork and colors", None),
            ("displays", "Monitor layout", None),
            ("animations", "Animation playback", None),
        ):
            group = make_group(title, description)
            self._page_boxes[name].append(group)
            section_groups[name] = group
        self.enabled = Adw.SwitchRow()
        self.respect_inhibitors = Adw.SwitchRow()
        self.respect_inhibitors.set_tooltip_text("Don't interrupt video, presentations, games or apps that inhibit idle/power management.")
        self.ignore_fullscreen = Adw.SwitchRow()
        self.ignore_fullscreen.set_tooltip_text("Don't start automatically when the foreground window is fullscreen. Requires optional KWin helper on Wayland.")
        self.delay = Gtk.SpinButton.new_with_range(10, 86400, 10)
        self.delay.set_numeric(True)
        self.font = Gtk.FontDialogButton.new(Gtk.FontDialog())
        self.font.set_hexpand(False)
        self.background = Gtk.ColorDialogButton.new(Gtk.ColorDialog())
        self.background.set_tooltip_text("Background color of the terminal; affects all monitors unless independently configured")
        self.frame_rate = Gtk.SpinButton.new_with_range(1, 240, 1)
        self.frame_rate.set_numeric(True)
        self.effect_hold = Gtk.SpinButton.new_with_range(0, 120, 0.5)
        self.effect_hold.set_digits(1)
        self.effect_hold.set_tooltip_text("Keep the completed logo visible before the next animation. Set 0 for immediate transitions.")
        self.speed = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 2.0, 0.1)
        self.speed.set_digits(1)
        self.speed.set_hexpand(True)
        self.speed.set_tooltip_text("Frame pacing multiplier. Lower values slow visual updates; some timed effects may not change total duration.")
        self.duration_factor = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 10.0, 0.5)
        self.time_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 2.0, 0.1)
        self.simulation_hold = Gtk.SpinButton.new_with_range(1, 10, 1)
        self.simulation_hold.set_tooltip_text("Repeat each generated frame at the FPS cap without advancing the animation. 2 means roughly half-speed animation while retaining output cadence. Uses the reference Rust renderer.")
        self.time_scale.set_digits(1)
        self.time_scale.set_hexpand(True)
        self.time_scale.set_tooltip_text("Changes the internal clock for effects driven by elapsed time. Does not alter FPS cap. Frame-step-based effects do not respond to this control.")
        self.duration_factor.set_digits(1)
        self.duration_factor.set_hexpand(True)
        self.duration_factor.set_tooltip_text("Time dilation of ttfx frame delays. 2× keeps each animation step twice as long; it also lowers actual FPS. This is not independent simulation-time scaling.")
        # Always show min, max and current values, not hover-only tooltips.
        for slider, minimum, maximum, low, high in (
            (self.speed, 0.1, 2.0, "0.1×", "2.0×"),
            (self.duration_factor, 0.5, 10.0, "0.5×", "10×"),
            (self.time_scale, 0.1, 2.0, "0.1×", "2.0×"),
        ):
            slider.set_draw_value(True)
            slider.set_value_pos(Gtk.PositionType.RIGHT)
            slider.set_size_request(180, -1)
            slider.set_hexpand(True)
        self.override_effect_colors = Adw.SwitchRow()
        self.override_effect_colors.set_tooltip_text("Off keeps the animations' original RGB colors; your palette still colors unstyled effects.")
        self.cycle_palette = Adw.SwitchRow()
        self.palette_ping_pong = Adw.SwitchRow()
        self.palette_ping_pong.set_tooltip_text("Go from first to last color and back without jumping from last to first. For palettes with three or more colors.")
        self.palette_steps = Gtk.SpinButton.new_with_range(1, 120, 1)
        self.palette_steps.set_tooltip_text("1 means a different palette color each effect. Higher values interpolate gradually between effects, never during one effect.")
        self.per_monitor_visuals = Adw.SwitchRow()
        self.auto_fit_artwork = Adw.SwitchRow()
        self.auto_fit_artwork.set_tooltip_text("Fit the artwork in independent or shared monitor mode. Off always restores your saved font size.")
        self.auto_fit_artwork.connect("notify::active", self._refresh_fit_warnings)
        self.palette_entries = []
        self.palette_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.palette_box.set_hexpand(True)
        self.palette_swatches = Gtk.FlowBox()
        self.palette_swatches.set_selection_mode(Gtk.SelectionMode.NONE)
        self.palette_swatches.set_min_children_per_line(1)
        self.palette_swatches.set_max_children_per_line(MAX_COLORS)
        self.palette_swatches.set_column_spacing(8)
        self.palette_swatches.set_row_spacing(8)
        self.palette_box.append(self.palette_swatches)
        palette_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.palette_add = Gtk.Button(label="Add color")
        self.palette_add.connect("clicked", lambda *_: self._add_shared_color())
        self.palette_remove = Gtk.Button(label="Remove last")
        self.palette_remove.connect("clicked", lambda *_: self._remove_shared_color())
        self.palette_reset = Gtk.Button.new_from_icon_name("edit-undo-symbolic")
        self.palette_reset.set_tooltip_text("Restore default palette")
        self.palette_reset.connect("clicked", lambda *_: self._replace_shared_palette(reset_colors()))
        for button in (self.palette_add, self.palette_remove, self.palette_reset):
            palette_actions.append(button)
        self.palette_box.append(palette_actions)
        self._replace_shared_palette(DEFAULT_CONFIG["palette"])

        self.section_groups = section_groups
    def _color_button(self, color, position, scope):
        rgba = Gdk.RGBA()
        if not rgba.parse(color):
            raise ValueError(f"Invalid palette color: {color}")
        button = Gtk.ColorDialogButton.new(Gtk.ColorDialog())
        button.set_tooltip_text(f"{scope} color {position}")
        button.set_rgba(rgba)
        # Reset must react immediately to a manually changed swatch, not only
        # to Add/Remove. This callback runs even for the initial widgets.
        if scope == "Shared palette":
            button.connect("notify::rgba", self._update_shared_reset)
        if getattr(self, "_monitor_signals_connected", False):
            button.connect("notify::rgba", self._mark_dirty)
            if scope == "Shared palette":
                button.connect("notify::rgba", self._refresh_gallery_palette)
        return button

    def _update_shared_reset(self, *_unused):
        if hasattr(self, "palette_reset"):
            colors = tuple(self._rgba_hex(button) for button in self.palette_entries)
            self.palette_reset.set_sensitive(colors != reset_colors())
        # Per-monitor reset restores the *current* shared palette, not factory
        # colors; refresh its affordance whenever that palette is edited.
        for connector in getattr(self, "monitor_palette_buttons", {}):
            self._update_monitor_reset(connector)

    def _update_monitor_reset(self, connector):
        actions = getattr(self, "monitor_palette_actions", {}).get(connector)
        if actions is None:
            return
        existing = tuple(self._rgba_hex(button) for button in self.monitor_palette_buttons[connector])
        fallback = tuple(self._rgba_hex(button) for button in self.palette_entries)
        actions[2].set_sensitive(existing != fallback)

    def _replace_shared_palette(self, colors):
        from palette_editor_model import validate_palette
        colors = validate_palette(colors)
        was_loading = getattr(self, "_loading_preferences", False)
        self._loading_preferences = True
        try:
            for button in self.palette_entries:
                self.palette_swatches.remove(button.get_parent())
            self.palette_entries.clear()
            for index, color in enumerate(colors, 1):
                button = self._color_button(color, index, "Shared palette")
                self.palette_entries.append(button)
                self.palette_swatches.insert(button, -1)
            self.palette_add.set_sensitive(len(colors) < MAX_COLORS)
            self.palette_remove.set_sensitive(len(colors) > 1)
            self.palette_reset.set_sensitive(tuple(colors) != reset_colors())
        finally:
            self._loading_preferences = was_loading
        self._update_shared_reset()
        if hasattr(self, "_saved_snapshot") and not was_loading:
            self._mark_dirty()
            self._refresh_gallery_palette()

    def _add_shared_color(self):
        self._replace_shared_palette(add_color([self._rgba_hex(b) for b in self.palette_entries]))

    def _remove_shared_color(self):
        self._replace_shared_palette(remove_color([self._rgba_hex(b) for b in self.palette_entries]))

    def _replace_monitor_palette(self, connector, colors):
        from palette_editor_model import validate_palette
        colors = validate_palette(colors)
        swatches = self.monitor_palette_flows[connector]
        existing = self.monitor_palette_buttons[connector]
        was_loading = self._loading_preferences
        self._loading_preferences = True
        try:
            for button in existing:
                swatches.remove(button.get_parent())
            existing.clear()
            for index, color in enumerate(colors, 1):
                button = self._color_button(color, index, self.monitor_labels[connector])
                button.connect("notify::rgba", lambda *_args, monitor=connector:
                               self._update_monitor_reset(monitor))
                swatches.insert(button, -1)
                existing.append(button)
            plus, minus, reset = self.monitor_palette_actions[connector]
            plus.set_sensitive(len(colors) < MAX_COLORS)
            minus.set_sensitive(len(colors) > 1)
            reset.set_sensitive(tuple(colors) != tuple(self._rgba_hex(b) for b in self.palette_entries))
        finally:
            self._loading_preferences = was_loading
        if hasattr(self, "_saved_snapshot") and not was_loading:
            self._mark_dirty()

    def _add_monitor_color(self, connector):
        buttons = self.monitor_palette_buttons[connector]
        self._replace_monitor_palette(connector, add_color([self._rgba_hex(b) for b in buttons]))

    def _remove_monitor_color(self, connector):
        buttons = self.monitor_palette_buttons[connector]
        self._replace_monitor_palette(connector, remove_color([self._rgba_hex(b) for b in buttons]))

    def _make_monitor_widgets(self):
        general = self._page_boxes["general"]
        appearance = self._page_boxes["appearance"]
        displays = self._page_boxes["displays"]
        animations = self._page_boxes["animations"]
        preview_page = self._page_boxes["preview"]
        # State-only GTK control retained for save/snapshot compatibility; the
        # user-facing selector exists only in Effect Library (B214).
        # Controls the Effect Library Play button; never changes idle activation.
        # Separate is the default so the gallery retains its entire scroll area.
        self.effect_preview_mode = Gtk.DropDown.new_from_strings([
            "Separate window",
            "Pinned in library",
        ])
        self.effect_preview_mode.set_tooltip_text(
            "Separate opens a large window that stays open during keyboard/mouse input. "
            "Pinned keeps a compact live terminal below the scrollable effect cards."
        )
        self.playlist_mode = Adw.SwitchRow()
        self.playlist_mode.set_tooltip_text("Play effects in your ordered playlists instead of choosing randomly. Use Playlist Editor to arrange them.")
        self.per_monitor = Adw.SwitchRow()
        self.per_monitor.set_tooltip_text("Off: same effects and display settings on both screens. On: separate FPS, palette and artwork per monitor, with optional synchronized effects.")
        self.shared_effect = Adw.SwitchRow()
        self.shared_effect.set_tooltip_text("Same effect sequence across screens. Waits for slowest monitor between effects; exact frames may differ.")
        self.monitor_rates_group = make_group("Per-display frame rates")
        self.monitor_colors_group = make_group("Per-display palettes")
        self.monitor_artwork_group = make_group("Per-display artwork")
        self.monitor_spins = {}
        self.monitor_labels = {}
        self.monitor_palette_buttons = {}
        self.monitor_palette_flows = {}
        self.monitor_palette_actions = {}
        self.monitor_artwork_entries = {}
        self.monitor_artwork_labels = {}
        # Keep disconnected display widgets in memory, but detach their rows.
        # This preserves unsaved edits when a monitor is unplugged and returned.
        self._monitor_rows = {}
        self._monitor_connected = set()
        self._sync_monitor_widgets()

    def _create_monitor_widgets(self, connector, label, config):
        """Create the three rows for a newly connected display exactly once."""
        self.monitor_labels[connector] = label
        spin = Gtk.SpinButton.new_with_range(1, 240, 1)
        spin.set_value(config.get("monitor_fps", {}).get(connector, config["frame_rate"]))
        rate_row = adaptive_action_row(self.monitor_rates_group, label, spin, "Output FPS cap")
        install_numeric_reset(rate_row, spin, default_for("frame_rate"), Gtk)
        self.monitor_spins[connector] = spin

        # The palette editor wraps naturally, with a bounded count per display.
        palette_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        swatches = Gtk.FlowBox()
        swatches.set_selection_mode(Gtk.SelectionMode.NONE)
        swatches.set_min_children_per_line(1)
        swatches.set_max_children_per_line(MAX_COLORS)
        swatches.set_column_spacing(6)
        swatches.set_row_spacing(4)
        palette_layout.append(swatches)
        palette_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        add_color_button = Gtk.Button(label="Add color")
        add_color_button.connect("clicked", lambda *_: self._add_monitor_color(connector))
        remove_color_button = Gtk.Button(label="Remove last")
        remove_color_button.connect("clicked", lambda *_: self._remove_monitor_color(connector))
        reset_color_button = Gtk.Button.new_from_icon_name("edit-undo-symbolic")
        reset_color_button.set_tooltip_text("Use shared palette colors")
        reset_color_button.connect("clicked", lambda *_: self._replace_monitor_palette(
            connector, [self._rgba_hex(b) for b in self.palette_entries]))
        for button in (add_color_button, remove_color_button, reset_color_button):
            palette_actions.append(button)
        palette_layout.append(palette_actions)
        palette_row = adaptive_action_row(self.monitor_colors_group, f"{label} · Palette", palette_layout)
        self.monitor_palette_flows[connector] = swatches
        self.monitor_palette_buttons[connector] = []
        self.monitor_palette_actions[connector] = (add_color_button, remove_color_button, reset_color_button)
        colors = config.get("monitor_visuals", {}).get(connector, {}).get("palette", config["palette"])
        self._replace_monitor_palette(connector, colors)

        artwork = Gtk.Entry()
        artwork.set_text(config.get("monitor_artwork", {}).get(connector, ""))
        artwork_label = Gtk.Label(xalign=1, ellipsize=Pango.EllipsizeMode.MIDDLE)
        artwork_label.set_max_width_chars(17)
        self.monitor_artwork_entries[connector] = artwork
        self.monitor_artwork_labels[connector] = artwork_label
        picker = Gtk.Button(label="Choose…")
        picker.set_tooltip_text("Add or choose a text artwork file")
        picker.connect("clicked", self._choose_monitor_artwork, connector)
        editor = Gtk.Button(label="Edit")
        editor.set_tooltip_text("Open this monitor's artwork in your text editor")
        editor.connect("clicked", self._edit_monitor_artwork, connector)
        reset = Gtk.Button.new_from_icon_name("edit-undo-symbolic")
        reset.add_css_class("flat")
        reset.set_tooltip_text("Use default artwork")
        reset.connect("clicked", lambda _button, e=artwork: e.set_text(""))

        def selection_changed(entry, *_args, lbl=artwork_label, btn=reset):
            selected = entry.get_text()
            lbl.set_text(Path(selected).name if selected else "Default")
            btn.set_opacity(1 if selected else 0)
            btn.set_sensitive(bool(selected))
            btn.set_focusable(bool(selected))

        artwork.connect("changed", selection_changed)
        selection_changed(artwork)
        picker_box = Gtk.FlowBox()
        picker_box.set_selection_mode(Gtk.SelectionMode.NONE)
        picker_box.set_min_children_per_line(1)
        picker_box.set_max_children_per_line(4)
        picker_box.set_column_spacing(6)
        picker_box.set_row_spacing(4)
        for item in (artwork_label, editor, picker, reset):
            picker_box.insert(item, -1)
        artwork_row = adaptive_action_row(self.monitor_artwork_group, f"{label} · Artwork", picker_box,
                                 "Text files in ~/.config/ascii-saver/artworks/")
        self._monitor_rows[connector] = (rate_row, palette_row, artwork_row)

        # The initial set of monitor widgets is connected later by
        # _connect_dirty_signals. Hot-plugged widgets need connections now.
        if getattr(self, "_monitor_signals_connected", False):
            spin.connect("value-changed", self._mark_dirty)
            artwork.connect("changed", self._mark_dirty)

    def _sync_monitor_widgets(self):
        """Reconcile GDK monitor changes without dropping edits or stored rows."""
        from monitor_config import extend_monitor_baseline

        artwork_group = getattr(self, 'monitor_artwork_group', self.monitor_colors_group)
        display = Gdk.Display.get_default()
        model = display.get_monitors() if display else None
        targets = {}
        if model:
            for index in range(model.get_n_items()):
                monitor = model.get_item(index)
                connector = monitor.get_connector() or monitor.get_model() or f"Display {index + 1}"
                targets[connector] = f"Display {index + 1}: {monitor.get_model() or 'Monitor'}"

        new = set(targets) - set(self._monitor_rows)
        old = self._monitor_connected - set(targets)
        returned = set(targets) - self._monitor_connected - new
        was_loading = self._loading_preferences
        self._loading_preferences = True
        try:
            for connector in old:
                fps_row, palette_row, artwork_row = self._monitor_rows[connector]
                self.monitor_rates_group.remove(fps_row)
                self.monitor_colors_group.remove(palette_row)
                artwork_group.remove(artwork_row)
            config = load_config(ctl.config_file) if new else None
            for connector in targets:
                if connector in new:
                    self._create_monitor_widgets(connector, targets[connector], config)
                elif connector in returned:
                    fps_row, palette_row, artwork_row = self._monitor_rows[connector]
                    self.monitor_rates_group.add(fps_row)
                    self.monitor_colors_group.add(palette_row)
                    artwork_group.add(artwork_row)
                label = targets[connector]
                self.monitor_labels[connector] = label
                fps_row, palette_row, artwork_row = self._monitor_rows[connector]
                fps_row.set_title(label)
                palette_row.set_title(f"{label} · Palette")
                artwork_row.set_title(f"{label} · Artwork")
            self._monitor_connected = set(targets)
        finally:
            self._loading_preferences = was_loading
        if new and hasattr(self, "_saved_snapshot"):
            self._saved_snapshot = extend_monitor_baseline(
                self._saved_snapshot, self._preference_snapshot(), new)
        if hasattr(self, "_saved_snapshot") and not self._loading_preferences:
            self._mark_dirty()
        return new, old

    def _edit_monitor_artwork(self, _button, connector):
        """Always open an editor, even when no .txt handler is configured."""
        from artwork_editor import ArtworkEditor
        relative = self.monitor_artwork_entries[connector].get_text() or "logo.txt"
        base = ctl.config_dir.resolve()
        target = (base / relative).resolve()
        if not target.is_relative_to(base) or not target.is_file():
            self._set_notice("Artwork file not found.", error=True)
            return
        if not hasattr(self, "_artwork_editors"):
            self._artwork_editors = {}
        existing = self._artwork_editors.get(connector)
        if existing is not None:
            existing.present()
            return
        def finished(message):
            # This only runs after a real close or a confirmed discard.
            self._artwork_editors.pop(connector, None)
            self._set_notice(message)

        try:
            editor = ArtworkEditor(self, target, on_finished=finished, config_dir=ctl.config_dir)
        except (OSError, UnicodeError) as error:
            self._set_notice(f"Cannot open artwork: {error}", error=True)
            return
        self._artwork_editors[connector] = editor
        editor.present()

    def _choose_monitor_artwork(self, _button, connector):
        """GTK file picker, not a raw path entry; imported files stay editable."""
        from pathlib import Path
        import ctl
        from gi.repository import Gio
        library = ctl.config_dir / "artworks"
        library.mkdir(parents=True, exist_ok=True)
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose ASCII artwork")
        dialog.set_initial_folder(Gio.File.new_for_path(str(library)))
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Text artwork (*.txt)")
        file_filter.add_pattern("*.txt")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)
        dialog.set_filters(filters)
        def selected(chooser, result):
            try:
                chosen = chooser.open_finish(result)
                if chosen is None or not chosen.get_path():
                    return
                from artwork_library import import_artwork_file
                relative = import_artwork_file(Path(chosen.get_path()), ctl.config_dir)
                self.monitor_artwork_entries[connector].set_text(relative)
                self._refresh_fit_warnings()
            except GLib.Error as error:
                # Closing the file dialog without choosing is not an error.
                if "dismiss" not in str(error).lower() and "cancel" not in str(error).lower():
                    self._set_notice(f"Cannot select artwork: {error}", error=True)
            except (OSError, ValueError) as error:
                self._set_notice(f"Cannot import artwork: {error}", error=True)
        dialog.open(self, None, selected)
