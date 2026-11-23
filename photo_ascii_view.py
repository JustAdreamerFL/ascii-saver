"""GTK Artwork Studio photo importer with responsive live source / ASCII view.

The source photo is never edited or moved. User must explicitly choose Use in
Editor (dirty-buffer confirmation handled by ArtworkEditor) or Save as New.
"""
from __future__ import annotations

from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Adw, Gio, GLib, GdkPixbuf
from window_shortcuts import install_close_shortcuts

from photo_ascii import (AVAILABLE_RAMPS, CUSTOM_RAMP_NAME, DEFAULT_CUSTOM_RAMP,
                         PhotoSettings, photo_to_ascii, validate_custom_ramp)
from photo_presets import list_presets, save_preset, delete_preset
from photo_project import (SOURCE_EXTENSIONS, load_photo_project,
                           save_photo_project)


class PhotoAsciiWindow(Adw.Window):
    def __init__(self, parent, config_dir: Path, on_use, saved_reference: str | None = None):
        super().__init__(transient_for=parent, title='Photo to ASCII')
        install_close_shortcuts(self, Gtk, Gdk)
        self.set_default_size(1040, 760)
        self.config_dir = Path(config_dir)
        self._on_use = on_use
        self._pixbuf = None
        self._source_bytes = None
        self._source_extension = None
        self._loading_project = False
        self._artwork = ''
        self._refresh_id = None

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)
        open_button = Gtk.Button(label='Open Photo')
        open_button.connect('clicked', self._choose_image)
        header.pack_start(open_button)
        self.use_button = Gtk.Button(label='Use in Editor')
        self.use_button.set_tooltip_text('Replace the current editor buffer. Saving there will overwrite that existing artwork.')
        self.use_button.set_sensitive(False)
        self.use_button.connect('clicked', self._use_in_editor)
        header.pack_end(self.use_button)

        scroller = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main.set_margin_start(16)
        main.set_margin_end(16)
        main.set_margin_top(16)
        main.set_margin_bottom(16)
        scroller.set_child(main)
        toolbar.set_content(scroller)
        self.toasts = Adw.ToastOverlay()
        self.toasts.set_child(toolbar)
        self.set_content(self.toasts)

        intro = Gtk.Label(label='Turn a photo into editable ASCII art. Adjust the essentials, then save a new artwork or continue in the editor.',
                          xalign=0, wrap=True)
        intro.add_css_class('dim-label')
        main.append(intro)

        compare = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, hexpand=True)
        main.append(compare)
        source_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                                 hexpand=True, vexpand=True)
        source_section.append(Gtk.Label(label='Original photo', xalign=0, css_classes=['heading']))
        self.photo = Gtk.Picture()
        self.photo.set_can_shrink(True)
        self.photo.set_size_request(210, 230)
        self.photo.set_content_fit(Gtk.ContentFit.CONTAIN)
        source_section.append(self.photo)
        self.filename = Gtk.Label(label='Choose a local image to start', xalign=0, wrap=True)
        self.filename.add_css_class('dim-label')
        source_section.append(self.filename)
        compare.append(source_section)

        ascii_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                                hexpand=True, vexpand=True)
        ascii_section.append(Gtk.Label(label='Live ASCII preview', xalign=0, css_classes=['heading']))
        self.preview = Gtk.TextView(editable=False, cursor_visible=False, monospace=True,
                                    left_margin=10, right_margin=10, top_margin=10,
                                    bottom_margin=10)
        self.preview.set_wrap_mode(Gtk.WrapMode.NONE)
        preview_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        preview_scroll.set_size_request(210, 260)
        preview_scroll.set_min_content_height(230)
        preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_scroll.set_child(self.preview)
        ascii_section.append(preview_scroll)
        compare.append(ascii_section)
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 770sp'))
        narrow.add_setter(compare, 'orientation', Gtk.Orientation.VERTICAL)
        self.add_breakpoint(narrow)

        # Curated styles are immediately discoverable. Personal preset editing
        # stays inside a collapsed section so beginners see only Look/Apply.
        looks = Adw.PreferencesGroup(title='Start with a creative look',
                                     description='Try a style, then make it your own. Applying a look changes the preview, never a saved artwork.')
        main.append(looks)
        self.look = Adw.ComboRow(title='Look')
        looks.add(self.look)
        use_look_row = Adw.ActionRow(title='Try selected look',
                                     subtitle='Apply its photo-to-ASCII settings. You can adjust everything afterward.')
        self.apply_look_button = Gtk.Button(label='Apply Look', valign=Gtk.Align.CENTER)
        self.apply_look_button.connect('clicked', self._apply_selected_preset)
        use_look_row.add_suffix(self.apply_look_button)
        looks.add(use_look_row)
        self.personal_presets = Adw.ExpanderRow(title='My conversion presets',
                                               subtitle='Save and reuse your favorite settings')
        self.personal_presets.set_expanded(False)
        looks.add(self.personal_presets)
        self.preset_name = Adw.EntryRow(title='New preset name')
        self.personal_presets.add_row(self.preset_name)
        save_row = Adw.ActionRow(title='Save current settings',
                                 subtitle='Save a new personal look, without changing the photo or artwork')
        self.save_preset_button = Gtk.Button(label='Save Preset', valign=Gtk.Align.CENTER)
        self.save_preset_button.set_sensitive(False)
        self.save_preset_button.connect('clicked', self._save_custom_preset)
        save_row.add_suffix(self.save_preset_button)
        self.personal_presets.add_row(save_row)
        delete_row = Adw.ActionRow(title='Remove selected preset',
                                   subtitle='Only personal presets can be removed; built-in looks are permanent')
        self.delete_preset_button = Gtk.Button(label='Remove', valign=Gtk.Align.CENTER)
        self.delete_preset_button.add_css_class('destructive-action')
        self.delete_preset_button.set_sensitive(False)
        self.delete_preset_button.connect('clicked', self._confirm_delete_preset)
        delete_row.add_suffix(self.delete_preset_button)
        self.personal_presets.add_row(delete_row)
        self.preset_name.connect('notify::text', self._preset_name_changed)
        self.look.connect('notify::selected', self._selected_preset_changed)

        basic = Adw.PreferencesGroup(title='Adjust your artwork',
                                     description='Good defaults first. The preview updates as you adjust.')
        main.append(basic)
        self.columns = Adw.SpinRow.new_with_range(16, 120, 2)
        self.columns.set_title('Width (characters)')
        self.columns.set_digits(0)
        self.columns.set_value(70)
        basic.add(self.columns)
        self.rows = Adw.SpinRow.new_with_range(8, 60, 1)
        self.rows.set_title('Height (lines)')
        self.rows.set_digits(0)
        self.rows.set_value(28)
        basic.add(self.rows)
        self.fit = Adw.ComboRow(title='Framing')
        fit_model = Gtk.StringList.new(['Fill frame (center crop)', 'Keep full photo (pad with spaces)'])
        self.fit.set_model(fit_model)
        basic.add(self.fit)
        self.ramp = Adw.ComboRow(title='ASCII style')
        self.ramp.set_model(Gtk.StringList.new(list(AVAILABLE_RAMPS)))
        basic.add(self.ramp)
        self.brightness = Adw.SpinRow.new_with_range(-100, 100, 5)
        self.brightness.set_title('Brightness')
        self.brightness.set_digits(0)
        self.brightness.set_subtitle('0 is the original brightness')
        basic.add(self.brightness)
        self.contrast = Adw.SpinRow.new_with_range(0, 200, 5)
        self.contrast.set_title('Contrast')
        self.contrast.set_digits(0)
        self.contrast.set_value(100)
        basic.add(self.contrast)
        self.invert = Adw.SwitchRow(title='Invert light and dark')
        basic.add(self.invert)

        # Secondary controls remain undisclosed until needed. This is a
        # built-in editor, not a specialist image-processing dashboard.
        self.advanced = Adw.ExpanderRow(title='Advanced image tools',
                                        subtitle='Gamma, detail, custom characters and finishing')
        self.advanced.set_expanded(False)
        basic.add(self.advanced)
        self.gamma = Adw.SpinRow.new_with_range(0.5, 2.5, 0.1)
        self.gamma.set_title('Gamma')
        self.gamma.set_subtitle('1.0 is neutral; higher values brighten midtones')
        self.gamma.set_digits(1)
        self.gamma.set_value(1.0)
        self.advanced.add_row(self.gamma)
        self.edge = Adw.SpinRow.new_with_range(0, 100, 10)
        self.edge.set_title('Edge definition')
        self.edge.set_subtitle('Emphasize local detail without changing the photo')
        self.edge.set_digits(0)
        self.advanced.add_row(self.edge)
        self.dither = Adw.SwitchRow(title='Dithering',
                                    subtitle='Mix different character densities to smooth gradients')
        self.advanced.add_row(self.dither)
        self.posterize = Adw.ComboRow(title='Posterization',
                                      subtitle='Limit tones for bold, graphic shapes')
        self.posterize.set_model(Gtk.StringList.new(
            ['Off'] + [f'{n} tones' for n in range(2, 9)]))
        self.advanced.add_row(self.posterize)
        self.alpha_background = Adw.ComboRow(title='Transparent pixels',
                                             subtitle='Background for transparent PNG or WebP images')
        self.alpha_background.set_model(Gtk.StringList.new(['White', 'Gray', 'Black']))
        self.alpha_background.set_sensitive(False)
        self.advanced.add_row(self.alpha_background)
        self.custom_ramp = Adw.EntryRow(title='Custom characters: dark to light')
        self.custom_ramp.set_text(DEFAULT_CUSTOM_RAMP)
        self.custom_ramp.set_sensitive(False)
        self.advanced.add_row(self.custom_ramp)
        self.advanced.add_row(Adw.ActionRow(
            title='Character ramp guide',
            subtitle='Type 2–63 different ASCII symbols, darkest first. A blank for highlights is added automatically.'))
        self.ramp.connect('notify::selected', self._ramp_selected)
        reset_row = Adw.ActionRow(title='Restore advanced defaults',
                                  subtitle='Neutral gamma, no edge boost or dithering, default custom symbols, no posterization, white background')
        reset_button = Gtk.Button(label='Reset', valign=Gtk.Align.CENTER)
        reset_button.connect('clicked', self._reset_advanced)
        reset_row.add_suffix(reset_button)
        self.advanced.add_row(reset_row)

        for widget, signal in ((self.columns, 'notify::value'),
                               (self.rows, 'notify::value'),
                               (self.brightness, 'notify::value'),
                               (self.contrast, 'notify::value'),
                               (self.fit, 'notify::selected'),
                               (self.ramp, 'notify::selected'),
                               (self.invert, 'notify::active'),
                               (self.gamma, 'notify::value'),
                               (self.edge, 'notify::value'),
                               (self.dither, 'notify::active'),
                               (self.posterize, 'notify::selected'),
                               (self.alpha_background, 'notify::selected'),
                               (self.custom_ramp, 'notify::text')):
            widget.connect(signal, self._schedule_refresh)

        export = Adw.PreferencesGroup(title='Keep your artwork',
                                      description='Save an editable project containing your original photo, conversion settings and a separate ASCII .txt asset.')
        main.append(export)
        self.art_name = Adw.EntryRow(title='Artwork name')
        self.art_name.set_text('photo-art')
        export.add(self.art_name)
        self.save_new_button = Gtk.Button(label='Save as New Artwork', halign=Gtk.Align.START)
        self.save_new_button.add_css_class('suggested-action')
        self.save_new_button.set_sensitive(False)
        self.save_new_button.connect('clicked', self._save_new)
        main.append(self.save_new_button)
        note = Gtk.Label(label='The source photo and settings are stored with each new artwork. Reopen the artwork later to continue converting. Use in Editor changes the open text only after its own Save.', xalign=0, wrap=True)
        note.add_css_class('dim-label')
        main.append(note)
        self.status = Gtk.Label(label='No photo loaded', xalign=0, wrap=True)
        self.status.add_css_class('dim-label')
        main.append(self.status)
        self._load_presets()
        self.connect('close-request', self._closing)
        if saved_reference is not None:
            self._open_saved_project(saved_reference)

    def _load_presets(self, select_key=None):
        try:
            self._presets, skipped = list_presets(self.config_dir)
        except (ValueError, OSError) as error:
            # A bad personal library must not disable the built-in looks.
            from photo_presets import BUILTIN_PRESETS
            self._presets, skipped = list(BUILTIN_PRESETS), 0
            self._show_error(f'Personal presets unavailable: {error}')
        self.look.set_model(Gtk.StringList.new([item.name for item in self._presets]))
        chosen = next((i for i, item in enumerate(self._presets)
                       if item.key == select_key), 0)
        self.look.set_selected(chosen)
        self._selected_preset_changed()
        if skipped:
            self.toasts.add_toast(Adw.Toast.new(f'Skipped {skipped} invalid preset file(s).'))

    def _selected_preset(self):
        position = self.look.get_selected()
        return self._presets[position] if 0 <= position < len(self._presets) else None

    def _selected_preset_changed(self, *_unused):
        preset = self._selected_preset()
        self.apply_look_button.set_sensitive(preset is not None)
        self.delete_preset_button.set_sensitive(preset is not None and not preset.builtin)
        self.look.set_subtitle(preset.description if preset is not None else 'Choose a creative style')

    def _preset_name_changed(self, *_unused):
        self.save_preset_button.set_sensitive(bool(self.preset_name.get_text().strip()))

    def _apply_settings(self, settings):
        # Suppress intermediate renders while ten controls are updated.
        self._loading_project = True
        try:
            self.columns.set_value(settings.columns)
            self.rows.set_value(settings.rows)
            self.fit.set_selected(0 if settings.fit == 'crop' else 1)
            self.custom_ramp.set_text(settings.custom_ramp)
            self.ramp.set_selected(AVAILABLE_RAMPS.index(settings.ramp))
            self.custom_ramp.set_sensitive(settings.ramp == CUSTOM_RAMP_NAME)
            self.brightness.set_value(settings.brightness)
            self.contrast.set_value(settings.contrast)
            self.invert.set_active(settings.invert)
            self.gamma.set_value(settings.gamma)
            self.edge.set_value(settings.edge)
            self.dither.set_active(settings.dither)
            self.posterize.set_selected(0 if settings.posterize == 0 else settings.posterize - 1)
            self.alpha_background.set_selected(('white', 'gray', 'black').index(settings.alpha_background))
        finally:
            self._loading_project = False
        # Render even when no pending debounce was scheduled.
        if self._refresh_id is not None:
            GLib.source_remove(self._refresh_id)
            self._refresh_id = None
        if settings.ramp == CUSTOM_RAMP_NAME:
            self.advanced.set_expanded(True)
        self._refresh()

    def _ramp_selected(self, *_unused):
        selected = self.ramp.get_selected()
        is_custom = (0 <= selected < len(AVAILABLE_RAMPS) and
                     AVAILABLE_RAMPS[selected] == CUSTOM_RAMP_NAME)
        self.custom_ramp.set_sensitive(is_custom)
        if is_custom and not self._loading_project:
            self.advanced.set_expanded(True)

    def _apply_selected_preset(self, *_unused):
        preset = self._selected_preset()
        if preset is None:
            return
        self._apply_settings(preset.settings)
        self.toasts.add_toast(Adw.Toast.new(f'Applied {preset.name}. Fine-tune it below.'))

    def _save_custom_preset(self, *_unused):
        try:
            saved = save_preset(self.config_dir, self.preset_name.get_text(), self._settings())
        except (OSError, ValueError) as error:
            self._show_error(f'Could not save preset: {error}')
            return
        self._load_presets(select_key=saved.key)
        self.preset_name.set_text('')
        self.toasts.add_toast(Adw.Toast.new(f'Saved personal preset: {saved.name}'))

    def _confirm_delete_preset(self, *_unused):
        preset = self._selected_preset()
        if preset is None or preset.builtin:
            return
        if hasattr(Adw, 'AlertDialog'):
            dialog = Adw.AlertDialog.new('Remove personal preset?',
                                          f'This removes “{preset.name}” from your presets. Current image settings and saved artwork are unchanged.')
            modern = True
        else:
            dialog = Adw.MessageDialog.new(self, 'Remove personal preset?',
                                             f'This removes “{preset.name}” from your presets. Current image settings and saved artwork are unchanged.')
            modern = False
        dialog.add_response('cancel', 'Cancel')
        dialog.add_response('remove', 'Remove')
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.set_response_appearance('remove', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect('response', lambda _dialog, response: (
            self._remove_custom_preset(preset.key) if response == 'remove' else None))
        if modern:
            dialog.present(self)
        else:
            dialog.present()

    def _remove_custom_preset(self, key):
        try:
            delete_preset(self.config_dir, key)
        except (OSError, ValueError) as error:
            self._show_error(f'Could not remove preset: {error}')
            return
        self._load_presets()
        self.toasts.add_toast(Adw.Toast.new('Personal preset removed. Current artwork is unchanged.'))

    def _reset_advanced(self, *_unused):
        # Every changed control schedules the same coalesced preview update.
        self.gamma.set_value(1.0)
        self.edge.set_value(0)
        self.dither.set_active(False)
        self.posterize.set_selected(0)
        self.alpha_background.set_selected(0)
        self.custom_ramp.set_text(DEFAULT_CUSTOM_RAMP)

    def _choose_image(self, *_unused):
        dialog = Gtk.FileDialog()
        dialog.set_title('Open Photo')
        file_filter = Gtk.FileFilter()
        file_filter.set_name('Images (PNG, JPEG, WebP, BMP)')
        for kind in ('image/png', 'image/jpeg', 'image/webp', 'image/bmp'):
            file_filter.add_mime_type(kind)
        model = Gio.ListStore.new(Gtk.FileFilter)
        model.append(file_filter)
        dialog.set_filters(model)
        dialog.open(self, None, self._image_chosen)

    def _image_chosen(self, dialog, result):
        try:
            chosen = dialog.open_finish(result)
        except GLib.Error as error:
            if error.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                return
            self._show_error(f'Could not open the image: {error.message}')
            return
        if chosen is None or not chosen.get_path():
            self._show_error('Choose a local image file.')
            return
        path = Path(chosen.get_path())
        try:
            self._load_source(path)
        except (OSError, ValueError, GLib.Error) as error:
            self._show_error(f'Could not open the image: {error}')
            return
        self.art_name.set_text(path.stem)
        self._refresh()

    def _load_source(self, path: Path):
        """Keep the original photo bytes in memory for an editable export."""
        if not path.is_file() or not 0 < path.stat().st_size <= 25_000_000:
            raise ValueError('Image must be a local file smaller than 25 MB.')
        info = GdkPixbuf.Pixbuf.get_file_info(str(path))
        if info is None:
            raise ValueError('Not a supported image.')
        image_format, full_width, full_height = info
        if full_width < 1 or full_height < 1 or full_width * full_height > 60_000_000:
            raise ValueError('Image dimensions are too large.')
        formats = {'jpeg': '.jpg', 'png': '.png', 'webp': '.webp', 'bmp': '.bmp'}
        extension = formats.get(image_format.get_name().lower())
        if extension not in SOURCE_EXTENSIONS:
            raise ValueError('Only PNG, JPEG, WebP and BMP are supported.')
        before = path.stat()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path), 1200, 1200, True)
        data = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('The photo changed while it was being opened. Retry the import.')
        if pixbuf.get_n_channels() not in (3, 4):
            raise ValueError('Image must be RGB or RGBA.')
        self._source_bytes = data
        self._source_extension = extension
        self._pixbuf = pixbuf
        self.alpha_background.set_sensitive(pixbuf.get_has_alpha())
        self.photo.set_pixbuf(pixbuf)
        self.filename.set_text(path.name)

    def _open_saved_project(self, reference: str):
        try:
            project = load_photo_project(self.config_dir, reference)
            self._load_source(project.source_path)
            self._apply_settings(project.settings)
            self.art_name.set_text(Path(reference).stem)
            if project.text_modified:
                self.status.set_text('Photo recipe loaded. This artwork also has manual text changes, which are not applied to the photo conversion. Saving a new variant will preserve both.')
            else:
                self.status.set_text('Photo recipe reopened. Adjust the conversion, then Save as New Artwork to keep the original.')
        except (OSError, ValueError, GLib.Error) as error:
            self._show_error(f'Could not reopen photo project: {error}')

    def _settings(self):
        # An incomplete custom string must not block a standard ramp after
        # switching away. Store only a safe default while Custom is inactive.
        custom = self.custom_ramp.get_text()
        if AVAILABLE_RAMPS[self.ramp.get_selected()] != CUSTOM_RAMP_NAME:
            try:
                validate_custom_ramp(custom)
            except ValueError:
                custom = DEFAULT_CUSTOM_RAMP
        return PhotoSettings(columns=int(self.columns.get_value()),
                             rows=int(self.rows.get_value()),
                             fit='crop' if self.fit.get_selected() == 0 else 'fit',
                             brightness=int(self.brightness.get_value()),
                             contrast=int(self.contrast.get_value()),
                             invert=self.invert.get_active(),
                             ramp=AVAILABLE_RAMPS[self.ramp.get_selected()],
                             custom_ramp=custom,
                             gamma=round(self.gamma.get_value(), 1),
                             edge=int(self.edge.get_value()),
                             dither=self.dither.get_active(),
                             posterize=0 if self.posterize.get_selected() == 0 else self.posterize.get_selected() + 1,
                             alpha_background=('white', 'gray', 'black')[self.alpha_background.get_selected()])

    def _schedule_refresh(self, *_unused):
        if self._loading_project or self._pixbuf is None or self._refresh_id is not None:
            return
        self._refresh_id = GLib.timeout_add(80, self._refresh)

    def _refresh(self):
        self._refresh_id = None
        if self._pixbuf is None:
            return GLib.SOURCE_REMOVE
        buf = self._pixbuf
        try:
            artwork = photo_to_ascii(bytes(buf.get_pixels()), buf.get_width(), buf.get_height(),
                                     channels=buf.get_n_channels(),
                                     rowstride=buf.get_rowstride(), settings=self._settings())
        except (ValueError, IndexError) as error:
            self._artwork = ''
            self.preview.get_buffer().set_text('')
            self.use_button.set_sensitive(False)
            self.save_new_button.set_sensitive(False)
            # An unfinished character ramp is a normal editing state, not a
            # reason to flood the screen with an error toast on every keypress.
            self.status.set_text(f'Adjust your conversion settings: {error}')
            return GLib.SOURCE_REMOVE
        self._artwork = artwork
        self.preview.get_buffer().set_text(artwork)
        self.use_button.set_sensitive(True)
        self.save_new_button.set_sensitive(True)
        self.status.set_text(f'{int(self.columns.get_value())} columns × {int(self.rows.get_value())} lines · preview updated')
        return GLib.SOURCE_REMOVE

    def _ensure_latest_preview(self):
        # The user may click Export during the 80 ms debounce. Never export a
        # previous setting while the visible control already shows a new one.
        if self._refresh_id is not None:
            GLib.source_remove(self._refresh_id)
            self._refresh_id = None
            self._refresh()

    def _use_in_editor(self, *_unused):
        self._ensure_latest_preview()
        if self._artwork:
            self._on_use(self._artwork, self)

    def _save_new(self, *_unused):
        self._ensure_latest_preview()
        if not self._artwork or self._source_bytes is None:
            return
        try:
            reference = save_photo_project(self.config_dir, self.art_name.get_text(),
                                           self._artwork, self._source_bytes,
                                           self._source_extension, self._settings())
        except (OSError, ValueError) as error:
            self._show_error(f'Could not save artwork: {error}')
            return
        self.status.set_text(f'Saved {reference} with its editable photo project. Select it in the artwork picker to use or reopen it.')
        self.toasts.add_toast(Adw.Toast.new(f'Saved as {reference}'))

    def _show_error(self, message):
        self.status.set_text(message)
        self.toasts.add_toast(Adw.Toast.new(message))

    def _closing(self, *_unused):
        if self._refresh_id is not None:
            GLib.source_remove(self._refresh_id)
            self._refresh_id = None
        return False
