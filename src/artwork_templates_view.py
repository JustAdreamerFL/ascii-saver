"""Beginner-first template chooser with an adaptive ASCII preview.

The chooser never writes files. Choosing a template hands it to ArtworkEditor,
which keeps the explicit Save/Discard workflow for the actual artwork file.
"""
from __future__ import annotations

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
from window_shortcuts import install_close_shortcuts
from artwork_templates import TEMPLATES


class ArtworkTemplatesWindow(Adw.Window):
    def __init__(self, parent, on_use, action_label="Use Template"):
        super().__init__(transient_for=parent, title='Explore ASCII styles')
        install_close_shortcuts(self, Gtk, Gdk)
        self.set_default_size(860, 620)
        self._on_use = on_use
        self._rows = {}
        self._row_templates = {}

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)
        choose = Gtk.Button(label=action_label)
        choose.add_css_class('suggested-action')
        choose.connect('clicked', self._use_selected)
        header.pack_end(choose)
        self.choose_button = choose

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(12)
        content.set_margin_bottom(16)
        intro = Gtk.Label(label='Choose a creative direction, then make it yours in the editor.',
                          xalign=0, wrap=True)
        intro.add_css_class('dim-label')
        content.append(intro)

        columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16,
                          hexpand=True, vexpand=True)
        content.append(columns)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                       hexpand=True, vexpand=True)
        label = Gtk.Label(label='Styles', xalign=0)
        label.add_css_class('heading')
        left.append(label)
        self.search = Gtk.SearchEntry(placeholder_text='Search styles')
        self.search.connect('search-changed', self._update_filter)
        left.append(self.search)
        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class('boxed-list')
        self.listbox.set_filter_func(self._filter_row)
        self.listbox.connect('row-selected', self._selected)
        for template in TEMPLATES:
            row = Gtk.ListBoxRow()
            details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            details.set_margin_top(10)
            details.set_margin_bottom(10)
            details.set_margin_start(12)
            details.set_margin_end(12)
            title = Gtk.Label(label=template.title, xalign=0)
            title.add_css_class('heading')
            subtitle = Gtk.Label(label=template.style, xalign=0, wrap=True)
            subtitle.add_css_class('dim-label')
            details.append(title)
            details.append(subtitle)
            row.set_child(details)
            # Register metadata before appending: ListBox may call its filter
            # synchronously while inserting the new row.
            self._rows[template.key] = row
            self._row_templates[row] = template
            self.listbox.append(row)
        left_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        left_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        left_scroll.set_min_content_height(150)
        left_scroll.set_child(self.listbox)
        left.append(left_scroll)
        columns.append(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                        hexpand=True, vexpand=True)
        preview_title = Gtk.Label(label='Preview', xalign=0)
        preview_title.add_css_class('heading')
        right.append(preview_title)
        self.description = Gtk.Label(xalign=0, wrap=True)
        self.description.add_css_class('dim-label')
        right.append(self.description)
        self.preview = Gtk.TextView(editable=False, cursor_visible=False, monospace=True,
                                    left_margin=12, right_margin=12, top_margin=12,
                                    bottom_margin=12)
        self.preview.set_wrap_mode(Gtk.WrapMode.NONE)
        preview_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        preview_scroll.set_min_content_height(190)
        preview_scroll.set_child(self.preview)
        right.append(preview_scroll)
        columns.append(right)
        toolbar.set_content(content)
        self.set_content(toolbar)

        # One consistent source/preview arrangement across desktop sizes.
        # Adw restores the horizontal orientation when the breakpoint ends.
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 690sp'))
        narrow.add_setter(columns, 'orientation', Gtk.Orientation.VERTICAL)
        self.add_breakpoint(narrow)
        self.listbox.select_row(self._rows[TEMPLATES[0].key])

    def _filter_row(self, row):
        query = self.search.get_text().strip().casefold()
        template = self._row_templates[row]
        return not query or query in f'{template.title} {template.style} {template.description}'.casefold()

    def _update_filter(self, *_unused):
        self.listbox.invalidate_filter()
        selected = self.listbox.get_selected_row()
        if selected is None or not self._filter_row(selected):
            for template in TEMPLATES:
                row = self._rows[template.key]
                if self._filter_row(row):
                    self.listbox.select_row(row)
                    return
            self.listbox.unselect_all()
        self.choose_button.set_sensitive(self.listbox.get_selected_row() is not None)

    def _selected(self, _listbox, row):
        self.choose_button.set_sensitive(row is not None)
        if row is None:
            self.description.set_text('No matching styles. Try another search.')
            self.preview.get_buffer().set_text('')
            return
        template = self._row_templates[row]
        self.description.set_text(template.description)
        self.preview.get_buffer().set_text(template.artwork)

    def _use_selected(self, *_unused):
        row = self.listbox.get_selected_row()
        if row is None:
            return
        template = self._row_templates[row]
        self._on_use(template, self)
