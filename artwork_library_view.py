"""Accessible, offline Artwork Studio library with responsive text previews.

Existing assets open in their own editor. Selecting or filtering never changes
an already-open editor buffer or writes to disk.
"""
from __future__ import annotations

from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango, Gdk
from window_shortcuts import install_close_shortcuts

from artwork_catalog import (ArtworkMetadata, LocalArtwork, filter_artworks, list_artworks,
                             save_metadata, _orient, _safe_preview)
from artwork_history import read_history
from artwork_library import save_generated_artwork


class ArtworkLibraryWindow(Adw.Window):
    def __init__(self, parent, config_dir: Path):
        super().__init__(transient_for=parent, title='My Artwork')
        install_close_shortcuts(self, Gtk, Gdk)
        self.set_default_size(930, 650)
        self.config_dir = Path(config_dir)
        self._assets = []
        self._rows = {}
        self._opened_editors = {}
        self._template_picker = None
        self._online_picker = None
        self._selected_reference = None
        self._closed = False
        self.connect("close-request", self._closing)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)
        add_template = Gtk.Button(label='From Template')
        add_template.set_tooltip_text('Save an original creative template as your own new artwork')
        add_template.connect('clicked', self._from_template)
        refresh = Gtk.Button(label='Refresh')
        refresh.set_tooltip_text('Rescan your locally saved artwork files')
        refresh.connect('clicked', self._refresh)
        header.pack_start(refresh)
        browse_online = Gtk.Button(label='Browse Online')
        browse_online.set_tooltip_text('Explore the community ascii-bin collection; imports are optional')
        browse_online.connect('clicked', self._browse_online)
        self.open_button = Gtk.Button(label='Open Artwork')
        self.open_button.add_css_class('suggested-action')
        self.open_button.set_sensitive(False)
        self.open_button.connect('clicked', self._open_artwork)
        header.pack_end(self.open_button)
        self.tags_button = Gtk.Button(label='Details')
        self.tags_button.set_sensitive(False)
        self.tags_button.connect('clicked', self._edit_tags)
        header.pack_end(self.tags_button)

        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        frame.set_margin_start(16)
        frame.set_margin_end(16)
        frame.set_margin_top(12)
        frame.set_margin_bottom(16)
        discovery_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        add_template.set_hexpand(True)
        browse_online.set_hexpand(True)
        discovery_actions.append(add_template)
        discovery_actions.append(browse_online)
        frame.append(discovery_actions)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search = Gtk.SearchEntry(placeholder_text='Search names, tags, authors and descriptions')
        self.search.set_hexpand(True)
        self.search.connect('search-changed', self._apply_filter)
        controls.append(self.search)
        self.history_filter = Gtk.DropDown.new_from_strings(['All artwork', 'Recently used'])
        self.history_filter.connect('notify::selected', self._apply_filter)
        controls.append(self.history_filter)
        self.kind = Gtk.DropDown.new_from_strings(['All sources', 'Text artwork', 'Photo project'])
        self.kind.set_tooltip_text('Filter by source type')
        self.kind.connect('notify::selected', self._apply_filter)
        controls.append(self.kind)
        self.orientation = Gtk.DropDown.new_from_strings(['All shapes', 'Landscape', 'Square', 'Portrait'])
        self.orientation.set_tooltip_text('Filter by character-cell proportions')
        self.orientation.connect('notify::selected', self._apply_filter)
        controls.append(self.orientation)
        clear_filters = Gtk.Button(label='Clear Filters')
        clear_filters.set_tooltip_text('Show every saved artwork')
        clear_filters.connect('clicked', self._clear_filters)
        controls.append(clear_filters)
        frame.append(controls)

        panels = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16, hexpand=True, vexpand=True)
        frame.append(panels)
        listing = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, hexpand=True, vexpand=True)
        self.results = Gtk.Label(xalign=0, wrap=True)
        self.results.add_css_class('dim-label')
        listing.append(self.results)
        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class('boxed-list')
        self.listbox.connect('row-selected', self._selection_changed)
        scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(160)
        scroll.set_child(self.listbox)
        listing.append(scroll)
        panels.append(listing)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, hexpand=True, vexpand=True)
        info.append(Gtk.Label(label='Preview', xalign=0, css_classes=['heading']))
        self.meta = Gtk.Label(xalign=0, wrap=True, selectable=True)
        self.meta.add_css_class('dim-label')
        info.append(self.meta)
        self.preview = Gtk.TextView(editable=False, cursor_visible=False, monospace=True,
                                    left_margin=12, right_margin=12,
                                    top_margin=12, bottom_margin=12)
        self.preview.set_wrap_mode(Gtk.WrapMode.NONE)
        preview_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        preview_scroll.set_min_content_height(210)
        preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_scroll.set_child(self.preview)
        info.append(preview_scroll)
        panels.append(info)

        # No clipped preview or inaccessible filters at narrow widths.
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 730sp'))
        narrow.add_setter(panels, 'orientation', Gtk.Orientation.VERTICAL)
        narrow.add_setter(controls, 'orientation', Gtk.Orientation.VERTICAL)
        narrow.add_setter(discovery_actions, 'orientation', Gtk.Orientation.VERTICAL)
        self.add_breakpoint(narrow)

        toolbar.set_content(frame)
        self.toasts = Adw.ToastOverlay()
        self.toasts.set_child(toolbar)
        self.set_content(self.toasts)
        self._refresh()

    def _refresh(self, *_unused, select_reference=None):
        try:
            self._assets, skipped = list_artworks(self.config_dir)
            self._recent_references = read_history(self.config_dir)
            # The screensaver's default logo is editable too, not just
            # copies in artworks/. Present it as a real local asset.
            logo = self.config_dir / 'logo.txt'
            if logo.is_file() and not logo.is_symlink() and logo.stat().st_size < 2_000_000:
                text = logo.read_text(encoding='utf-8')
                lines = text.splitlines()
                cols = max((len(line.expandtabs(4)) for line in lines), default=0)
                self._assets.insert(0, LocalArtwork(
                    'logo.txt', 'Default artwork', _safe_preview(text), cols,
                    len(lines), _orient(cols, len(lines)), 'Text artwork', ()))
        except (OSError, ValueError) as error:
            self._assets, skipped = [], 0
            self._recent_references = []
            self.toasts.add_toast(Adw.Toast.new(f'Could not read artwork library: {error}'))
        self._skipped = skipped
        if select_reference is not None:
            self._selected_reference = select_reference
        self._apply_filter()

    def _apply_filter(self, *_unused):
        kind = ('All', 'Text artwork', 'Photo project')[self.kind.get_selected()]
        orientation = ('All', 'Landscape', 'Square', 'Portrait')[self.orientation.get_selected()]
        matches = filter_artworks(self._assets, self.search.get_text(), kind, orientation)
        if self.history_filter.get_selected() == 1:
            indexed = {item.reference: item for item in matches}
            matches = [indexed[ref] for ref in self._recent_references if ref in indexed]
        wanted_reference = self._selected_reference
        # Rebuild just this list. Nothing is changed in the artwork files.
        self.listbox.unselect_all()
        while (child := self.listbox.get_first_child()) is not None:
            self.listbox.remove(child)
        self._rows = {}
        for item in matches:
            row = Gtk.ListBoxRow()
            contents = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            contents.set_margin_start(12)
            contents.set_margin_end(12)
            contents.set_margin_top(9)
            contents.set_margin_bottom(9)
            title = Gtk.Label(label=item.title, xalign=0, ellipsize=Pango.EllipsizeMode.END)
            title.add_css_class('heading')
            detail = Gtk.Label(label=f'{item.kind} · {item.orientation} · {item.columns}×{item.rows}'
                               + (f' · {", ".join(item.tags)}' if item.tags else '')
                               + (f' · {item.author}' if item.author else ''),
                               xalign=0, ellipsize=Pango.EllipsizeMode.END)
            detail.add_css_class('dim-label')
            contents.append(title)
            contents.append(detail)
            # Lightweight visual thumbnail from the real artwork, never a
            # generated placeholder or an external screenshot.
            sample = '\n'.join(line[:52] for line in item.preview.splitlines()[:3])
            if sample:
                thumb = Gtk.Label(label=sample, xalign=0, ellipsize=Pango.EllipsizeMode.END)
                thumb.add_css_class('monospace')
                thumb.add_css_class('dim-label')
                contents.append(thumb)
            row.set_child(contents)
            # GTK may request selection synchronously while inserting rows.
            self._rows[row] = item
            self.listbox.append(row)
        message = f'{len(matches)} of {len(self._assets)} saved artworks'
        if self._skipped:
            message += f' · {self._skipped} unreadable or unsafe files skipped'
        if not matches:
            message += '. No matches. Clear search or change filters.'
        self.results.set_text(message)
        selected = next((row for row, asset in self._rows.items()
                         if asset.reference == wanted_reference), None)
        if selected is None and self._rows:
            selected = next(iter(self._rows))
        if selected is not None:
            self.listbox.select_row(selected)
        else:
            self._selection_changed(self.listbox, None)

    def _clear_filters(self, *_unused):
        self.search.set_text('')
        self.history_filter.set_selected(0)
        self.kind.set_selected(0)
        self.orientation.set_selected(0)
        self._apply_filter()

    def _selection_changed(self, _listbox, row):
        asset = self._rows.get(row)
        self.open_button.set_sensitive(asset is not None)
        self.tags_button.set_sensitive(asset is not None and asset.reference != 'logo.txt')
        self._selected_reference = asset.reference if asset else None
        if asset is None:
            self.meta.set_text('Choose an artwork to see its preview.')
            self.preview.get_buffer().set_text('')
            return
        self.meta.set_text(f'{asset.reference}\n{asset.kind} · {asset.orientation} '
                           f'· {asset.columns} columns × {asset.rows} lines'
                           + (f'\nTags: {", ".join(asset.tags)}' if asset.tags else '\nNo tags yet')
                           + (f'\nAuthor: {asset.author}' if asset.author else '')
                           + (f'\nDescription: {asset.description}' if asset.description else '')
                           + (f'\nLicense: {asset.license}' if asset.license else '')
                           + (f'\nSource: {asset.source_url}' if asset.source_url else ''))
        self.preview.get_buffer().set_text(asset.preview)

    def _open_artwork(self, *_unused):
        ref = self._selected_reference
        if ref is None:
            return
        existing = self._opened_editors.get(ref)
        if existing is not None:
            existing.present()
            return
        from artwork_editor import ArtworkEditor
        from artwork_catalog import _art_path, _managed_root
        try:
            path = (self.config_dir / 'logo.txt') if ref == 'logo.txt' else _art_path(_managed_root(self.config_dir), ref)
            # Parent the actual editor to the original editor window, not this
            # chooser, so closing the chooser never discards an open document.
            parent = self.get_transient_for()
            window = ArtworkEditor(parent, path, config_dir=self.config_dir,
                                   on_finished=lambda _message: self._editor_closed(ref))
        except (OSError, ValueError, UnicodeError) as error:
            self.toasts.add_toast(Adw.Toast.new(f'Could not open artwork: {error}'))
            self._refresh()
            return
        self._opened_editors[ref] = window
        window.present()

    def _editor_closed(self, reference):
        self._opened_editors.pop(reference, None)
        if not self._closed:
            self._refresh(select_reference=reference)

    def _closing(self, *_unused):
        self._closed = True
        return False

    def _edit_tags(self, *_unused):
        """Edit tags and attribution together; original .txt stays untouched."""
        selected = next((a for a in self._assets if a.reference == self._selected_reference), None)
        if selected is None:
            return
        dialog = Adw.Window(transient_for=self, modal=True, title='Artwork Details')
        dialog.set_default_size(490, 460)
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        cancel = Gtk.Button(label='Cancel')
        cancel.connect('clicked', lambda *_: dialog.close())
        header.pack_start(cancel)
        save = Gtk.Button(label='Save Details')
        save.add_css_class('suggested-action')
        header.pack_end(save)
        toolbar.add_top_bar(header)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(12)
        content.set_margin_bottom(16)
        fields = {}
        for name, label, value in (
            ('tags', 'Tags (comma separated)', ', '.join(selected.tags)),
            ('author', 'Creator (leave blank if unknown)', selected.author),
            ('description', 'Description', selected.description),
            ('license', 'License (only if confirmed)', selected.license),
            ('source_url', 'Source HTTPS link', selected.source_url),
        ):
            content.append(Gtk.Label(label=label, xalign=0, wrap=True))
            entry = Gtk.Entry()
            entry.set_text(value)
            entry.set_hexpand(True)
            content.append(entry)
            fields[name] = entry
        feedback = Gtk.Label(xalign=0, wrap=True)
        feedback.add_css_class('dim-label')
        content.append(feedback)
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(content)
        toolbar.set_content(scroll)
        dialog.set_content(toolbar)

        def commit(*_unused):
            try:
                value = fields['tags'].get_text().strip()
                tags = tuple(tag.strip() for tag in value.split(',')) if value else ()
                save_metadata(self.config_dir, selected.reference, ArtworkMetadata(
                    tags, fields['author'].get_text(), fields['description'].get_text(),
                    fields['license'].get_text(), fields['source_url'].get_text()))
            except (ValueError, OSError) as error:
                feedback.set_text(f'Could not save artwork details: {error}')
                return
            dialog.close()
            self._refresh(select_reference=selected.reference)
            self.toasts.add_toast(Adw.Toast.new('Artwork details saved.'))

        save.connect('clicked', commit)
        dialog.present()

    def _browse_online(self, *_unused):
        if self._online_picker is not None:
            self._online_picker.present()
            return
        from artwork_online_view import OnlineArtworkWindow
        picker = OnlineArtworkWindow(self, self.config_dir, self._online_imported)
        self._online_picker = picker
        picker.connect('close-request', self._online_closed)
        picker.present()

    def _online_closed(self, *_unused):
        self._online_picker = None
        return False

    def _online_imported(self, reference):
        if not self._closed:
            self._refresh(select_reference=reference)

    def _from_template(self, *_unused):
        from artwork_templates_view import ArtworkTemplatesWindow
        if self._template_picker is not None:
            self._template_picker.present()
            return
        picker = ArtworkTemplatesWindow(self, self._save_template_copy,
                                        action_label='Save a Copy')
        self._template_picker = picker
        picker.connect('close-request', self._template_closed)
        picker.present()

    def _template_closed(self, *_unused):
        self._template_picker = None
        return False

    def _save_template_copy(self, template, picker):
        try:
            reference = save_generated_artwork(self.config_dir, template.title, template.artwork)
        except (ValueError, OSError) as error:
            self.toasts.add_toast(Adw.Toast.new(f'Could not save template: {error}'))
            return
        picker.close()
        self._refresh(select_reference=reference)
        self.toasts.add_toast(Adw.Toast.new('Template saved as a new artwork.'))
