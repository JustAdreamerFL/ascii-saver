#!/usr/bin/env python3
"""GTK4 editor for ordered ttfx playlists. Saves only on explicit Save."""
import sys
from pathlib import Path
import gi
gi.require_version('Gtk','4.0')
gi.require_version('Adw','1')
from gi.repository import Gtk, GLib, Adw, Gdk, Pango
import ctl
from helpers import load_config
from playlist_engine import EFFECTS, DEFAULT_PLAYLISTS, group, validate
from auto_playlists import PATTERNS, generate
from measured_playlists import generate_from_measurements
from animated_preview import AnimatedPreview, update_visible_previews
from palette_engine import palette_color_for_round
from effect_preview_window import EffectPreviewWindow
from window_shortcuts import install_close_shortcuts
from adwaita_ui import make_group, action_row
from edit_state import EditBaseline
from playlist_gallery_model import visible_effects, selection_caption
from effect_metadata import effect_caption

class Editor(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='ASCII Saver · Playlists', default_width=1020, default_height=730)
        install_close_shortcuts(self, Gtk, Gdk)
        raw=load_config(ctl.config_file)
        self.thumbnail_foreground = palette_color_for_round(raw, None, 0)
        self.thumbnail_background = raw.get('background', '#000000')
        self.items=[dict(p, effects=list(p['effects'])) for p in (raw.get('playlists') or DEFAULT_PLAYLISTS)]
        self._playlist_baseline = EditBaseline(self.items)
        self.current=0
        self.loading=False
        self.live_preview_window = None
        self._install_editor_styles()
        columns = Adw.NavigationSplitView()
        columns.set_vexpand(True)
        self.columns = columns

        # Playlist order is a real sidebar, not part of the effect gallery.
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        left.set_size_request(225, -1)
        left.set_margin_top(14)
        left.set_margin_bottom(14)
        left.set_margin_start(12)
        left.set_margin_end(12)
        left.append(Gtk.Label(label='Playlist order', xalign=0, css_classes=['heading']))
        left.append(Gtk.Label(label='Playlists run from top to bottom.',
                              xalign=0, wrap=True, css_classes=['dim-label']))
        self.chooser = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.chooser.add_css_class('navigation-sidebar')
        self.chooser.connect('row-selected', self.select)
        ls = Gtk.ScrolledWindow(min_content_height=280)
        ls.set_vexpand(True)
        ls.set_child(self.chooser)
        left.append(ls)
        buttons = Gtk.Box(spacing=6)
        for icon, callback, tip in [
            ('list-add-symbolic', self.add, 'Add playlist'),
            ('list-remove-symbolic', self.remove, 'Remove playlist'),
            ('go-up-symbolic', lambda _: self.move(-1), 'Move playlist up'),
            ('go-down-symbolic', lambda _: self.move(1), 'Move playlist down'),
        ]:
            button = Gtk.Button.new_from_icon_name(icon)
            button.set_tooltip_text(tip)
            button.set_hexpand(True)
            button.connect('clicked', callback)
            buttons.append(button)
        left.append(buttons)
        sidebar_toolbar = Adw.ToolbarView()
        sidebar_toolbar.add_top_bar(Adw.HeaderBar())
        sidebar_toolbar.set_content(left)
        columns.set_sidebar(Adw.NavigationPage(child=sidebar_toolbar, title="Playlists"))

        # The entire spare height goes to the effect gallery, not configuration.
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right.set_vexpand(True)
        right.set_hexpand(True)
        right.set_margin_top(12)
        right.set_margin_bottom(12)
        right.set_margin_start(14)
        right.set_margin_end(14)
        heading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        heading.append(Gtk.Label(label='Effect gallery', xalign=0, css_classes=['title-2']))
        self.selection_summary = Gtk.Label(xalign=0, css_classes=['dim-label'])
        self.selection_summary.set_ellipsize(Pango.EllipsizeMode.END)
        heading.append(self.selection_summary)
        right.append(heading)

        filters = Gtk.Box(spacing=8)
        self.search = Gtk.SearchEntry(hexpand=True)
        self.search.set_placeholder_text('Search 37 effects')
        self.search.connect('search-changed', self.refresh_effects)
        filters.append(self.search)
        self.duration = Gtk.DropDown.new_from_strings(['Any duration', 'Short', 'Medium', 'Long'])
        self.intensity = Gtk.DropDown.new_from_strings(['Any intensity', 'Gentle', 'Moderate', 'Energetic'])
        from adwaita_ui import center_string_dropdown
        for dropdown in (self.duration, self.intensity):
            center_string_dropdown(dropdown)
        self.duration.connect('notify::selected', self.refresh_effects)
        self.intensity.connect('notify::selected', self.refresh_effects)
        filters.append(self.duration)
        filters.append(self.intensity)
        right.append(filters)

        self.effects_box = Gtk.FlowBox()
        self.effects_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.effects_box.set_min_children_per_line(1)
        self.effects_box.set_max_children_per_line(3)
        self.effects_box.set_homogeneous(True)
        self.effects_box.set_hexpand(True)
        self.effects_box.set_valign(Gtk.Align.START)
        self.effects_box.set_row_spacing(12)
        self.effects_box.set_column_spacing(12)
        for name in ('set_margin_top', 'set_margin_bottom',
                     'set_margin_start', 'set_margin_end'):
            getattr(self.effects_box, name)(8)
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True, min_content_height=300)
        self.effect_scroller = scroll
        self.preview_entries = []
        scroll.get_vadjustment().connect('value-changed', self._sync_effect_previews)
        scroll.get_vadjustment().connect('changed', self._queue_effect_sync)
        scroll.connect('map', self._queue_effect_sync)
        scroll.set_child(self.effects_box)
        self.gallery_stack = Gtk.Stack()
        self.gallery_stack.set_vexpand(True)
        self.gallery_stack.set_hexpand(True)
        self.gallery_stack.add_named(scroll, 'gallery')
        empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        empty.set_valign(Gtk.Align.CENTER)
        empty.set_halign(Gtk.Align.CENTER)
        empty.append(Gtk.Label(label='No effects match these filters.',
                               wrap=True, justify=Gtk.Justification.CENTER,
                               css_classes=['title-3']))
        empty.append(Gtk.Label(label='Your playlist selection is unchanged.',
                               wrap=True, css_classes=['dim-label']))
        clear_filters = Gtk.Button(label='Clear filters')
        clear_filters.add_css_class('suggested-action')
        clear_filters.connect('clicked', self._clear_effect_filters)
        clear_filters.set_halign(Gtk.Align.CENTER)
        empty.append(clear_filters)
        self.gallery_stack.add_named(empty, 'empty')
        right.append(self.gallery_stack)

        # Secondary actions stay collapsed by default. Even when opened they
        # scroll inside a bounded panel, rather than shrinking the gallery to a
        # narrow strip at ordinary window heights.
        options = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        details = make_group('Current playlist')
        self.name = Adw.EntryRow(title="Playlist name")
        self.name.connect('changed', self.modify)
        details.add(self.name)
        self.enabled = Adw.SwitchRow(title="Enabled")
        self.enabled.connect('notify::active', self.modify)
        details.add(self.enabled)
        self.shuffle = Adw.SwitchRow(title='Shuffle effects', subtitle='Otherwise use the listed order')
        self.shuffle.connect('notify::active', self.modify)
        details.add(self.shuffle)
        options.append(details)

        generator_group = make_group('Automatic playlists')
        generator = Adw.ExpanderRow(title='Generate a playlist',
                                   subtitle='Replace the unsaved editor sequence')
        self.pattern = Gtk.DropDown.new_from_strings(list(PATTERNS))
        self.duration_pref = Gtk.DropDown.new_from_strings(['Any duration', 'Short', 'Medium', 'Long'])
        self.stage_size = Gtk.SpinButton.new_with_range(1, 12, 1)
        self.stage_size.set_value(4)
        for title, widget in (('Energy pattern', self.pattern),
                              ('Preferred duration', self.duration_pref),
                              ('Effects per stage', self.stage_size)):
            row = Adw.ActionRow(title=title)
            widget.set_valign(Gtk.Align.CENTER)
            row.add_suffix(widget)
            generator.add_row(row)
        go = Gtk.Button(label='Generate')
        go.connect('clicked', self.generate_playlists)
        row = Adw.ActionRow(title='Use suggested effect order',
                            subtitle='Replaces only the unsaved editor contents')
        row.add_suffix(go)
        generator.add_row(row)
        measured = Gtk.Button(label='Generate from measurements')
        measured.connect('clicked', self.generate_measured_playlists)
        row = Adw.ActionRow(title='Use measured durations',
                            subtitle='Duration estimates from effects you have run')
        row.add_suffix(measured)
        generator.add_row(row)
        generator_group.add(generator)
        options.append(generator_group)
        options_scroll = Gtk.ScrolledWindow()
        options_scroll.set_max_content_height(200)
        options_scroll.set_propagate_natural_height(True)
        options_scroll.set_child(options)
        self.options_revealer = Gtk.Revealer()
        self.options_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.options_revealer.set_child(options_scroll)
        right.append(self.options_revealer)

        self.status = Gtk.Label(label='Changes apply after Save and the next screensaver launch.',
                                xalign=0, hexpand=True, wrap=True, css_classes=['dim-label'])
        right.append(self.status)
        content_toolbar = Adw.ToolbarView()
        content_header = Adw.HeaderBar()
        self.options_button = Gtk.ToggleButton(label='Playlist options')
        self.options_button.set_tooltip_text('Edit playlist name, shuffle, and automatic generation')
        self.options_button.connect('toggled', self._toggle_playlist_options)
        content_header.pack_end(self.options_button)
        content_toolbar.add_top_bar(content_header)
        content_toolbar.set_content(right)
        columns.set_content(Adw.NavigationPage(child=content_toolbar, title="Effect gallery"))
        # The same Save/Discard behavior as Preferences and Effect Library:
        # contextual, visible on every navigation page, without reflow.
        self.unsaved_banner = Gtk.Revealer()
        self.unsaved_banner.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        banner_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        banner_row.add_css_class("card")
        banner_row.set_margin_top(10)
        banner_row.set_margin_start(12)
        banner_row.set_margin_end(12)
        banner_row.append(Gtk.Label(label="Unsaved playlist changes", xalign=0, hexpand=True))
        discard = Gtk.Button(label="Discard")
        discard.connect("clicked", self.discard)
        banner_row.append(discard)
        save = Gtk.Button(label="Save")
        save.add_css_class("suggested-action")
        save.connect("clicked", self.save)
        banner_row.append(save)
        self.unsaved_banner.set_child(banner_row)
        self.unsaved_banner.set_halign(Gtk.Align.FILL)
        self.unsaved_banner.set_valign(Gtk.Align.START)
        # Avoid covering the NavigationSplitView's actual headerbar controls.
        self.unsaved_banner.set_margin_top(56)
        overlay = Gtk.Overlay()
        overlay.set_child(columns)
        overlay.add_overlay(self.unsaved_banner)
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(overlay)
        self.set_content(self.toast_overlay)
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 700sp"))
        narrow.add_setter(columns, "collapsed", True)
        # These three controls previously forced a wide minimum size when
        # the navigation split collapsed. Stack them instead of clipping the
        # search field or duration/intensity dropdowns.
        narrow.add_setter(filters, "orientation", Gtk.Orientation.VERTICAL)
        self.add_breakpoint(narrow)
        self.populate()
        self._mark_playlist_dirty()
        # In-process editors must dispose their previews explicitly. When this
        # was a separate process, process exit hid any forgotten PTY/timer.
        self._closed = False
        self.connect('close-request', self._editor_closing)

    def _editor_closing(self, *_args):
        self._closed = True
        if self.live_preview_window is not None:
            self.live_preview_window.close()
            self.live_preview_window = None
        for _, preview in self.preview_entries:
            preview.release()
        self.preview_entries.clear()
        return False

    @staticmethod
    def _install_editor_styles():
        # Match the Effect Library card styling without adding a second hover
        # outline on the nested, keyboard-focusable thumbnail action.
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
        .playlist-effect-card {
            background: alpha(@theme_fg_color, 0.055);
            border: 1px solid alpha(@theme_fg_color, 0.14);
            border-radius: 12px;
            padding: 10px;
        }
        .playlist-effect-card.selected {
            border-color: alpha(@theme_selected_bg_color, 0.85);
        }
        .playlist-effect-card:hover {
            background: alpha(@theme_fg_color, 0.08);
        }
        .playlist-thumbnail-action, .playlist-thumbnail-action:hover {
            background: transparent;
            border: 0;
            box-shadow: none;
            padding: 0;
        }
        .playlist-thumbnail-action:focus-visible {
            outline: 2px solid @accent_color;
            outline-offset: 2px;
        }
        """)
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _toggle_playlist_options(self, button):
        self.options_revealer.set_reveal_child(button.get_active())

    def _update_selection_summary(self, visible_count=None):
        if not self.items:
            self.selection_summary.set_text('No playlists')
            return
        if visible_count is None:
            visible_count = len(visible_effects(
                EFFECTS,
                query=self.search.get_text(),
                duration=['any', 'short', 'medium', 'long'][self.duration.get_selected()],
                intensity=['any', 'gentle', 'moderate', 'energetic'][self.intensity.get_selected()],
            ))
        self.selection_summary.set_text(
            self.items[self.current]['name'] + ' · ' + selection_caption(
                self.items[self.current]['effects'], EFFECTS, visible_count))

    def _mark_playlist_dirty(self):
        self.unsaved_banner.set_reveal_child(self._playlist_baseline.changed(self.items))

    def discard(self, *_args):
        self.items = self._playlist_baseline.restore()
        self.current = min(self.current, len(self.items) - 1) if self.items else 0
        self.populate()
        self._mark_playlist_dirty()
        self.status.set_text("Changes discarded.")
        self.toast_overlay.add_toast(Adw.Toast.new("Playlist changes discarded."))

    def generate_playlists(self, _button):
        pattern=list(PATTERNS)[self.pattern.get_selected()]
        duration=['any','short','medium','long'][self.duration_pref.get_selected()]
        try:
            items=generate(pattern,duration,self.stage_size.get_value_as_int())
        except ValueError as error:
            self.status.set_text(str(error))
            return
        self.items=items
        self.current=0
        self.populate()
        self.status.set_text("Generated an editable sequence. Save to apply it.")
        self._mark_playlist_dirty()

    def generate_measured_playlists(self, _button):
        from pathlib import Path
        import os
        cache=Path(os.environ.get("XDG_CACHE_HOME",str(Path.home()/".cache"))) / "ascii-saver"
        pattern=list(PATTERNS)[self.pattern.get_selected()]
        duration=['any','short','medium','long'][self.duration_pref.get_selected()]
        try:
            items=generate_from_measurements(cache, pattern, duration, self.stage_size.get_value_as_int())
        except ValueError as error:
            self.status.set_text(str(error))
            return
        self.items=items
        self.current=0
        self.populate()
        self.status.set_text("Created editable playlists from measured durations. Save to apply.")
        self._mark_playlist_dirty()

    def populate(self):
        self.loading=True
        while row:=self.chooser.get_row_at_index(0):self.chooser.remove(row)
        for p in self.items:
            label=Gtk.Label(label=('● ' if p['enabled'] else '○ ')+p['name'],xalign=0,
                            margin_start=12,margin_end=12,margin_top=9,margin_bottom=9)
            row=Gtk.ListBoxRow();row.set_child(label);self.chooser.append(row)
        self.loading=False
        if self.items:
            self.current=min(self.current,len(self.items)-1)
            self.chooser.select_row(self.chooser.get_row_at_index(self.current))
            self.show_current()

    def select(self, box, row):
        if self.loading or row is None:return
        self.current=row.get_index();self.show_current()
        self.columns.set_show_content(True)

    def show_current(self):
        self.loading=True
        p=self.items[self.current]
        self.name.set_text(p['name']);self.enabled.set_active(p['enabled'])
        self.shuffle.set_active(p['order']=='shuffle')
        self.loading=False;self.refresh_effects()

    def modify(self,*args):
        if self.loading or not self.items:return
        p=self.items[self.current]
        p.update(name=self.name.get_text(), enabled=self.enabled.get_active(),order='shuffle' if self.shuffle.get_active() else 'sequential')
        self.chooser.get_row_at_index(self.current).get_child().set_text(('● ' if p['enabled'] else '○ ')+p['name'])
        self._update_selection_summary()
        self._mark_playlist_dirty()

    def _queue_effect_sync(self, *_args):
        if not getattr(self, '_closed', False):
            GLib.idle_add(self._sync_effect_previews)

    def _sync_effect_previews(self, *_args):
        if getattr(self, '_closed', False):
            return GLib.SOURCE_REMOVE
        return update_visible_previews(self.effect_scroller, self.preview_entries)

    def _clear_effect_filters(self, _button=None):
        # Reset all selectors together to avoid rebuilding up to 37 animated
        # cards three times. This is strictly a view action, not an edit.
        self._filter_update_suspended = True
        try:
            self.search.set_text('')
            self.duration.set_selected(0)
            self.intensity.set_selected(0)
        finally:
            self._filter_update_suspended = False
        self.refresh_effects()

    def refresh_effects(self,*args):
        if getattr(self, '_filter_update_suspended', False):
            return
        if not self.items:return
        for _, preview in self.preview_entries:
            preview.release()
        self.preview_entries.clear()
        while child:=self.effects_box.get_first_child():self.effects_box.remove(child)
        p=self.items[self.current]
        ds=['any','short','medium','long'][self.duration.get_selected()]
        ins=['any','gentle','moderate','energetic'][self.intensity.get_selected()]
        matches = visible_effects(EFFECTS, query=self.search.get_text(),
                                  duration=ds, intensity=ins)
        for effect in matches:
            category=group(effect)
            check=Gtk.CheckButton(label=effect)
            check.set_active(effect in p['effects'])
            check.set_hexpand(True)
            check.set_tooltip_text(f"Suggested duration: {category['duration']}; intensity: {category['intensity']}. Not measured.")
            tile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
            tile.add_css_class('playlist-effect-card')
            if check.get_active():
                tile.add_css_class('selected')
            tile.set_size_request(216, -1)
            path = ctl.data_dir / 'effects' / f'{effect}.aspr'
            # A click on the thumbnail toggles selection. The Play button is
            # separate so no actual renderer runs on a selection change.
            toggle_thumbnail = Gtk.Button()
            toggle_thumbnail.add_css_class('flat')
            toggle_thumbnail.add_css_class('playlist-thumbnail-action')
            toggle_thumbnail.set_tooltip_text(f'Toggle {effect} in this playlist')
            toggle_thumbnail.set_hexpand(True)
            if path.is_file():
                preview = AnimatedPreview(
                    path, width=196, height=84,
                    foreground=self.thumbnail_foreground,
                    background=self.thumbnail_background)
                toggle_thumbnail.set_child(preview)
                self.preview_entries.append((tile, preview))
            else:
                toggle_thumbnail.set_child(Gtk.Label(label='Preview unavailable'))
            toggle_thumbnail.connect('clicked', self._toggle_effect_thumbnail, check)
            tile.append(toggle_thumbnail)
            controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            controls.append(check)
            play = Gtk.Button.new_from_icon_name('media-playback-start-symbolic')
            play.set_tooltip_text(f'Play {effect} with your own artwork in a separate preview window')
            play.connect('clicked', self._play_effect, effect)
            controls.append(play)
            tile.append(controls)
            classification = Gtk.Label(label=effect_caption(effect), xalign=0)
            classification.add_css_class('dim-label')
            classification.set_tooltip_text('Suggested duration and intensity, not measured')
            tile.append(classification)
            check.connect('toggled',self.toggle_effect,effect,tile)
            self.effects_box.append(tile)
        self.gallery_stack.set_visible_child_name('gallery' if matches else 'empty')
        self._update_selection_summary(len(matches))
        self._queue_effect_sync()

    def _preview_window_closed(self, _window):
        self.live_preview_window = None
        return False

    def _toggle_effect_thumbnail(self, _button, checkbox):
        checkbox.set_active(not checkbox.get_active())

    def _play_effect(self, _button, effect):
        """Preview is an explicit, separate action from selecting an effect."""
        if self.live_preview_window is None:
            self.live_preview_window = EffectPreviewWindow(self)
            self.live_preview_window.connect('close-request', self._preview_window_closed)
        config = load_config(ctl.config_file)
        self.live_preview_window.play(effect, config.get('font', 'Monospace 12'))

    def toggle_effect(self,button,effect,tile=None):
        p=self.items[self.current]
        if button.get_active() and effect not in p['effects']:p['effects'].append(effect)
        elif not button.get_active() and effect in p['effects']:p['effects'].remove(effect)
        if tile is not None:
            if button.get_active():tile.add_css_class('selected')
            else:tile.remove_css_class('selected')
        self._update_selection_summary()
        self._mark_playlist_dirty()

    def add(self,*_):
        self.items.append(dict(name='New playlist',enabled=True,order='sequential',effects=['beams']))
        self.current=len(self.items)-1;self.populate()
        self._mark_playlist_dirty()

    def remove(self,*_):
        if len(self.items)<=1:
            self.status.set_text('Keep at least one playlist. Disable it if you do not want to use it.');return
        self.items.pop(self.current);self.populate()
        self._mark_playlist_dirty()

    def move(self,delta):
        nxt=self.current+delta
        if not 0<=nxt<len(self.items):return
        self.items[self.current],self.items[nxt]=self.items[nxt],self.items[self.current]
        self.current=nxt;self.populate()
        self._mark_playlist_dirty()

    def save(self,*_):
        try:
            playlists=validate(self.items)
            ctl.update_config_values({'playlists':playlists})
            self.items = [dict(p, effects=list(p['effects'])) for p in playlists]
            self._playlist_baseline.commit(self.items)
            self.populate()
            self._mark_playlist_dirty()
            self.status.set_text('Saved. The next screensaver launch uses these playlists.')
            self.toast_overlay.add_toast(Adw.Toast.new('Playlists saved.'))
        except (ValueError,OSError,SystemExit) as e:
            self.status.set_text(f'Cannot save: {e}')

if __name__ == '__main__':
    # Preserve the direct script entry point, but route it to the already
    # running ASCII Saver application (or start one if none is registered).
    # Never create an ungrouped, separately identified Playlists process.
    from settings import SettingsApplication

    Adw.init()
    sys.exit(SettingsApplication().run([sys.argv[0], '--playlist-editor']))
