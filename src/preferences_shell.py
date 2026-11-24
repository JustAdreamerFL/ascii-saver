"""Dedicated libadwaita preference screen builders."""
from __future__ import annotations
import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk
import ctl
from adwaita_ui import SettingsPage
from animated_preview import AnimatedPreview
from effect_catalog import EFFECTS
from pathlib import Path

class ShellBuilderMixin:
    def _make_shell(self):
        self.set_default_size(670, 660)
        self.set_size_request(360, 320)
        self._loading_preferences = True
        self._pending_changes = False
        self._closed = False

        # Native libadwaita pages with a single compact selector.
        # Avoid forcing a five-tab minimum width on narrow/tiled desktops.
        self.sections = Adw.ViewStack()
        self._page_boxes = {}
        for name, title, icon in (
            ("general", "General", "preferences-system-symbolic"),
            ("appearance", "Appearance", "applications-graphics-symbolic"),
            ("displays", "Displays", "video-display-symbolic"),
            ("animations", "Animations", "media-playlist-shuffle-symbolic"),
            ("preview", "Preview", "media-playback-start-symbolic"),
            ("tools", "Tools", "applications-utilities-symbolic"),
        ):
            page = SettingsPage()
            page.set_title(title)
            page.set_icon_name(icon)
            page_info = self.sections.add_titled(page, name, title)
            page_info.set_icon_name(icon)
            self._page_boxes[name] = page
        general = self._page_boxes["general"]
        appearance = self._page_boxes["appearance"]
        displays = self._page_boxes["displays"]
        animations = self._page_boxes["animations"]
        preview_page = self._page_boxes["preview"]

        # Preferences contain settings only. Renderer/watchdog process states
        # belong to the main dashboard, not among editable preferences.

        # Save / Discard live outside page scroll and appear only when dirty.
        self.unsaved_banner = Gtk.Revealer()
        banner_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        banner_row.add_css_class("unsaved-banner")
        banner_row.set_halign(Gtk.Align.END)
        banner_row.set_margin_start(12)
        banner_row.set_margin_end(12)
        banner_row.set_margin_top(8)
        banner_row.set_margin_bottom(8)
        # This action bar should never require a long descriptive label.
        # Hide the legacy label so Save/Discard fit even at 360sp.
        self.banner_label = Gtk.Label(label="Unsaved changes", xalign=0, hexpand=False)
        self.banner_label.set_visible(False)
        self.banner_discard = Gtk.Button(label="Discard")
        self.banner_discard.connect("clicked", self._discard_changes)
        banner_save = Gtk.Button(label="Save")
        banner_save.add_css_class("suggested-action")
        banner_save.connect("clicked", self._on_save)
        banner_row.append(self.banner_discard)
        banner_row.append(banner_save)
        self.unsaved_banner.set_child(banner_row)
        # Only one bar, hidden when clean. No permanent saved-state placeholder.
        self.unsaved_banner.set_reveal_child(False)
        self.unsaved_banner.set_visible(False)
        self.changes_tray = self.unsaved_banner

    def _make_navigation(self):
        """Single category selector, independent of the window minimum width.

        Five header tabs and an icon-based view switcher can force a minimum
        width greater than the available monitor space. That prevents the
        narrow breakpoint from ever activating and clips settings horizontally.
        Prefer one keyboard-accessible selector with the current page name.
        """
        names = ("general", "appearance", "displays", "animations", "preview", "tools")
        self.compact_categories = Gtk.DropDown.new_from_strings(
            ["General", "Appearance", "Displays", "Animations", "Preview", "Tools"])
        self.compact_categories.set_tooltip_text("Choose preferences section")
        self.compact_categories.set_size_request(130, -1)
        self._categories_sync = False

        def select_section(dropdown, *_args):
            if self._categories_sync:
                return
            index = dropdown.get_selected()
            if 0 <= index < len(names):
                self.sections.set_visible_child_name(names[index])

        def reflect_section(stack, *_args):
            selected = stack.get_visible_child_name()
            if selected in names:
                self._categories_sync = True
                try:
                    self.compact_categories.set_selected(names.index(selected))
                    self.navigation_list.select_row(self.navigation_rows[names.index(selected)])
                finally:
                    self._categories_sync = False

        self.compact_categories.connect("notify::selected", select_section)
        # Desktop sidebar and compact selector share the same ViewStack.
        self.wide_sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.wide_sidebar.set_size_request(180, -1)
        self.wide_sidebar.set_margin_top(18)
        self.wide_sidebar.set_margin_start(12)
        self.wide_sidebar.set_margin_end(8)
        self.wide_sidebar.set_visible(False)
        self.navigation_list = Gtk.ListBox()
        self.navigation_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.navigation_list.add_css_class("navigation-sidebar")
        self.navigation_rows = []
        for label in ("General", "Appearance", "Displays", "Animations", "Preview", "Tools"):
            row = Gtk.ListBoxRow()
            row.set_child(Gtk.Label(label=label, xalign=0, margin_start=12,
                                    margin_end=12, margin_top=9, margin_bottom=9))
            self.navigation_list.append(row)
            self.navigation_rows.append(row)
        self.navigation_list.connect("row-selected", lambda _list, row: (
            self.sections.set_visible_child_name(names[row.get_index()])
            if row is not None and not self._categories_sync else None))
        self.wide_sidebar.append(self.navigation_list)
        self.nav_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.nav_layout.append(self.wide_sidebar)
        self.nav_layout.append(self.sections)
        self.sections.set_hexpand(True)
        self.navigation_list.select_row(self.navigation_rows[0])
        self.header_title = Gtk.Label(label="Preferences", css_classes=["title"])
        self.header_title.set_visible(False)
        wide = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("min-width: 900sp"))
        wide.add_setter(self.wide_sidebar, "visible", True)
        wide.add_setter(self.compact_categories, "visible", False)
        wide.add_setter(self.header_title, "visible", True)

        def release_focus_for_layout_swap(*_args):
            # The breakpoint hides the focused compact selector. GTK then
            # relocates focus into the newly mapped navigation ListBox, whose
            # selection follows focus and would switch the visible page during
            # a resize. Drop focus before that relocation happens.
            self.set_focus(None)

        wide.connect("apply", release_focus_for_layout_swap)
        wide.connect("unapply", release_focus_for_layout_swap)
        self.add_breakpoint(wide)
        self.sections.connect("notify::visible-child-name", reflect_section)
        self.notice = Gtk.Label()  # Messages appear as toasts, not permanent rows.

        header = Adw.HeaderBar()
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_box.append(self.compact_categories)
        title_box.append(self.header_title)
        header.set_title_widget(title_box)
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.nav_layout)
        toolbar_view.set_content(self.toast_overlay)
        toolbar_view.add_bottom_bar(self.changes_tray)
        self.set_content(toolbar_view)
        # The fixed minimum is small enough for a tiled desktop, and does not
        # include a hidden wide tab widget in the size requisition.
        self.connect("close-request", self._preferences_closing)

