"""Opt-in online ASCII gallery with offline cache, preview and provenance.

Online feed I/O is never performed on GTK's UI thread. Import is a separate
user action and confirms the repository's uncertain individual rights.
"""
from __future__ import annotations

from pathlib import Path
from threading import Thread
import secrets

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Pango, Gdk
from window_shortcuts import install_close_shortcuts

from artwork_online import (PROVIDER_HOME, SOURCE_URL, LICENSE_NOTE,
                            load_collection, filter_collection, top_tags,
                            import_remote, sort_collection, SORT_OPTIONS, PAGE_SIZE)


class OnlineArtworkWindow(Adw.Window):
    def __init__(self, parent, config_dir: Path, on_import):
        super().__init__(transient_for=parent, title='Explore Online Artwork')
        install_close_shortcuts(self, Gtk, Gdk)
        self.set_default_size(930, 650)
        self.config_dir = Path(config_dir)
        self._on_import = on_import
        self._assets = ()
        self._rows = {}
        self._selected = None
        self._closed = False
        self._generation = 0
        self._tag_values = ['All']
        self._matches = []
        self._visible_count = 0
        self._shuffle_seed = secrets.randbits(64)
        self._loading = False
        self.connect('close-request', self._closing)

        view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        view.add_top_bar(header)
        self.refresh_button = Gtk.Button(label='Refresh Online')
        self.refresh_button.connect('clicked', self._refresh)
        header.pack_start(self.refresh_button)
        source = Gtk.LinkButton.new_with_label(PROVIDER_HOME, 'Provider & License')
        source.set_tooltip_text('Open ascii-bin on GitHub to read its terms and provenance notice')
        header.pack_start(source)
        self.import_button = Gtk.Button(label='Import a Copy')
        self.import_button.add_css_class('suggested-action')
        self.import_button.set_sensitive(False)
        self.import_button.connect('clicked', self._confirm_import)
        header.pack_end(self.import_button)

        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame.set_margin_start(16)
        frame.set_margin_end(16)
        frame.set_margin_top(12)
        frame.set_margin_bottom(16)
        warning = Gtk.Label(label='Community collection: CC0 is claimed, but rights to individual artworks are not verified. Review the source before reusing or publishing.',
                            xalign=0, wrap=True)
        warning.add_css_class('dim-label')
        warning.set_visible(False)  # Provider & License link remains in the header.
        frame.append(warning)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search = Gtk.SearchEntry(placeholder_text='Search descriptions and tags')
        self.search.set_hexpand(True)
        self.search.connect('search-changed', self._apply_filter)
        controls.append(self.search)
        self.tag = Gtk.DropDown.new_from_strings(['All'])
        self.tag.set_tooltip_text('Filter by online artwork tag')
        self.tag.connect('notify::selected', self._apply_filter)
        controls.append(self.tag)
        self.orientation = Gtk.DropDown.new_from_strings(['All shapes', 'Landscape', 'Square', 'Portrait'])
        self.orientation.connect('notify::selected', self._apply_filter)
        controls.append(self.orientation)
        self.sort = Gtk.DropDown.new_from_strings(list(SORT_OPTIONS))
        self.sort.set_tooltip_text('Reorder artworks without changing or downloading them')
        self.sort.connect('notify::selected', self._apply_filter)
        controls.append(self.sort)
        shuffle = Gtk.Button(label='Surprise Me')
        shuffle.set_tooltip_text('Discover a different random order of matching artworks')
        shuffle.connect('clicked', self._shuffle)
        controls.append(shuffle)
        reset = Gtk.Button(label='Clear Filters')
        reset.connect('clicked', self._clear_filters)
        controls.append(reset)
        frame.append(controls)

        panels = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16, hexpand=True, vexpand=True)
        frame.append(panels)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7, hexpand=True, vexpand=True)
        self.status = Gtk.Label(label='Online artwork has not been loaded.', xalign=0, wrap=True)
        self.status.add_css_class('dim-label')
        left.append(self.status)
        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class('boxed-list')
        self.listbox.connect('row-selected', self._selected_row)
        listing_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        listing_scroll.set_min_content_height(170)
        listing_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        listing_scroll.set_child(self.listbox)
        left.append(listing_scroll)
        self.show_more = Gtk.Button(label='Show More Artwork')
        self.show_more.set_visible(False)
        self.show_more.connect('clicked', self._load_more)
        left.append(self.show_more)
        panels.append(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, hexpand=True, vexpand=True)
        right.append(Gtk.Label(label='Preview', xalign=0, css_classes=['heading']))
        self.details = Gtk.Label(xalign=0, wrap=True, selectable=True)
        self.details.add_css_class('dim-label')
        right.append(self.details)
        self.preview = Gtk.TextView(editable=False, cursor_visible=False, monospace=True,
                                    left_margin=12, right_margin=12, top_margin=12, bottom_margin=12)
        self.preview.set_wrap_mode(Gtk.WrapMode.NONE)
        preview_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        preview_scroll.set_min_content_height(200)
        preview_scroll.set_child(self.preview)
        right.append(preview_scroll)
        panels.append(right)

        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 730sp'))
        breakpoint.add_setter(controls, 'orientation', Gtk.Orientation.VERTICAL)
        breakpoint.add_setter(panels, 'orientation', Gtk.Orientation.VERTICAL)
        self.add_breakpoint(breakpoint)
        view.set_content(frame)
        self.toasts = Adw.ToastOverlay()
        self.toasts.set_child(view)
        self.set_content(self.toasts)
        self._refresh()

    def _closing(self, *_unused):
        self._closed = True
        self._generation += 1
        return False

    def _refresh(self, *_unused):
        if self._closed or self._loading:
            return
        self._generation += 1
        generation = self._generation
        self._loading = True
        self.refresh_button.set_sensitive(False)
        self.status.set_text('Loading from ascii-bin…')
        self.import_button.set_sensitive(False)
        def worker():
            try:
                data = load_collection(self.config_dir)
                error = None
            except (OSError, ValueError) as exc:
                data, error = None, str(exc)
            GLib.idle_add(self._finished_load, generation, data, error)
        Thread(target=worker, daemon=True).start()

    def _finished_load(self, generation, result, error):
        if self._closed or generation != self._generation:
            return GLib.SOURCE_REMOVE
        self._loading = False
        self.refresh_button.set_sensitive(True)
        if error:
            # A refresh error must not destroy a collection already being
            # browsed. Loading without either memory or disk cache gives an
            # empty state with an actionable Refresh button.
            self._message = (f'Refresh failed: {error}. Showing last loaded collection.'
                             if self._assets else f'Could not load online artwork: {error}')
            self._apply_filter()
            return GLib.SOURCE_REMOVE
        self._assets, self._message = result
        current = self._tag_values[self.tag.get_selected()] if self.tag.get_selected() < len(self._tag_values) else 'All'
        self._tag_values = ['All', *top_tags(self._assets)]
        self.tag.set_model(Gtk.StringList.new(self._tag_values))
        self.tag.set_selected(self._tag_values.index(current) if current in self._tag_values else 0)
        self._apply_filter()
        return GLib.SOURCE_REMOVE

    def _shuffle(self, *_unused):
        # Surprise is a selection action, not merely a new sort order.
        # Retaining the previous row made the preview appear unchanged.
        from artwork_selection import choose_surprise
        match_ids = [art.number for art in self._matches]
        previous = self._selected.number if self._selected else None
        self._surprise_selection = choose_surprise(match_ids, previous)
        self._shuffle_seed = secrets.randbits(64)
        if self.sort.get_selected() != SORT_OPTIONS.index('Shuffle'):
            self.sort.set_selected(SORT_OPTIONS.index('Shuffle'))
        else:
            self._apply_filter()

    def _apply_filter(self, *_unused):
        tag_index = self.tag.get_selected()
        selected_tag = self._tag_values[tag_index] if tag_index < len(self._tag_values) else 'All'
        orientation = ('All', 'Landscape', 'Square', 'Portrait')[self.orientation.get_selected()]
        matches = filter_collection(self._assets, self.search.get_text(), selected_tag, orientation)
        self._matches = sort_collection(matches, SORT_OPTIONS[self.sort.get_selected()],
                                        seed=self._shuffle_seed)
        previous = getattr(self, '_surprise_selection', None)
        if previous is not None:
            # A selection on an unloaded page cannot be shown by Gtk.ListBox.
            # Move the surprise into the visible page without fetching thousands
            # of off-screen thumbnails.
            from artwork_selection import prioritize_selection
            self._matches = prioritize_selection(self._matches, previous)
        if previous is None:
            previous = self._selected.number if self._selected else None
        self._surprise_selection = None
        self.listbox.unselect_all()
        while (child := self.listbox.get_first_child()) is not None:
            self.listbox.remove(child)
        self._rows = {}
        self._visible_count = min(PAGE_SIZE, len(self._matches))
        self._append_rows(self._matches[:self._visible_count])
        self._update_status()
        chosen = next((r for r, art in self._rows.items() if art.number == previous), None)
        if chosen is None and self._rows:
            chosen = next(iter(self._rows))
        if chosen is not None:
            self.listbox.select_row(chosen)
        else:
            self._selected_row(None, None)

    def _append_rows(self, entries):
        # Render only a bounded page, never every remote artwork on each
        # search keystroke. The next page is appended without scroll jumps.
        for item in entries:
            row = Gtk.ListBoxRow()
            contents = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            for margin in ('start', 'end', 'top', 'bottom'):
                getattr(contents, 'set_margin_' + margin)(10)
            title = Gtk.Label(label=item.title, xalign=0, ellipsize=Pango.EllipsizeMode.END)
            title.add_css_class('heading')
            detail = Gtk.Label(label=f'{item.columns}×{item.rows} · {item.orientation}' +
                               (f' · {", ".join(item.tags[:3])}' if item.tags else ''),
                               xalign=0, ellipsize=Pango.EllipsizeMode.END)
            detail.add_css_class('dim-label')
            contents.append(title)
            contents.append(detail)
            thumb = Gtk.Label(label='\n'.join(line[:54] for line in item.preview.splitlines()[:3]),
                              xalign=0, ellipsize=Pango.EllipsizeMode.END)
            thumb.add_css_class('monospace')
            contents.append(thumb)
            row.set_child(contents)
            self._rows[row] = item
            self.listbox.append(row)

    def _update_status(self):
        self.show_more.set_visible(self._visible_count < len(self._matches))
        message = getattr(self, '_message', 'No online items loaded.')
        if not self._matches:
            self.status.set_text(f'0 matches from {len(self._assets)} artworks · {message}' +
                                 ' · Clear filters or refresh.' if self._assets else message)
        else:
            self.status.set_text(f'Showing {self._visible_count} of {len(self._matches)} matches '
                                 f'({len(self._assets)} total) · {message}')

    def _load_more(self, *_unused):
        if self._visible_count >= len(self._matches):
            return
        next_count = min(self._visible_count + PAGE_SIZE, len(self._matches))
        self._append_rows(self._matches[self._visible_count:next_count])
        self._visible_count = next_count
        self._update_status()

    def _clear_filters(self, *_unused):
        self.search.set_text('')
        self.tag.set_selected(0)
        self.orientation.set_selected(0)
        self._apply_filter()

    def _selected_row(self, _list, row):
        self._selected = self._rows.get(row)
        item = self._selected
        self.import_button.set_sensitive(item is not None and not self._loading)
        if item is None:
            self.details.set_text('Choose an artwork to preview its content and source.')
            self.preview.get_buffer().set_text('')
            return
        self.details.set_text(f'{item.title}\n{item.description or "No description provided"}\n'
                              f'Tags: {", ".join(item.tags) if item.tags else "None"}\n'
                              f'Author: unknown · {LICENSE_NOTE}\nSource: {SOURCE_URL}')
        self.preview.get_buffer().set_text(item.artwork)

    def _confirm_import(self, *_unused):
        item = self._selected
        if item is None or self._loading:
            return
        dialog = Adw.AlertDialog.new('Import this community artwork?',
            'The repository claims CC0, but individual creators and reuse rights are not verified. '
            'Import saves a separate local copy with its source and license warning. '
            'Please review rights before distributing it.')
        dialog.add_response('cancel', 'Cancel')
        dialog.add_response('import', 'Import a Copy')
        dialog.set_response_appearance('import', Adw.ResponseAppearance.SUGGESTED)
        dialog.connect('response', lambda _d, response: self._import(item) if response == 'import' else None)
        dialog.present(self)

    def _import(self, item):
        try:
            ref = import_remote(self.config_dir, item)
        except (OSError, ValueError) as error:
            self.toasts.add_toast(Adw.Toast.new(f'Import failed: {error}'))
            return
        self._on_import(ref)
        self.toasts.add_toast(Adw.Toast.new('Saved as a new artwork, with source details.'))
