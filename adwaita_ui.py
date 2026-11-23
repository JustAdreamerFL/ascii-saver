"""Shared libadwaita preference-building primitives.

The settings UI deliberately uses Adw.PreferencesPage/PreferencesGroup and
ActionRow; Gtk widgets remain for specialized controls without an Adw equivalent
(e.g. font chooser, color chooser, terminal animation). This module does not
own configuration or renderer state.
"""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Pango


class SettingsPage(Adw.PreferencesPage):
    """A real libadwaita preferences page with a convenience append method.

    Non-group widgets are given a dedicated group so they receive the same
    readable max-width and adaptive margins as other preference content.
    """

    def append(self, widget):
        if isinstance(widget, Adw.PreferencesGroup):
            self.add(widget)
        else:
            group = Adw.PreferencesGroup()
            group.add(widget)
            self.add(group)


def make_group(title, description=None):
    group = Adw.PreferencesGroup(title=title)
    if description:
        group.set_description(description)
    return group


def action_row(group, title, widget, subtitle=None):
    """Attach a control with a native boxed Adw.ActionRow.

    Existing Gtk control objects are kept intact: save, validation, defaults
    and dirty-state connections remain attached to the exact same object.
    """
    row = Adw.ActionRow(title=title)
    if subtitle:
        row.set_subtitle(subtitle)
    widget.set_valign(Gtk.Align.CENTER)
    # GTK Switch and CheckButton remain keyboard-accessible when their row is
    # activated; non-activatable controls still receive focus normally.
    if isinstance(widget, (Gtk.Switch, Gtk.CheckButton, Gtk.Button)):
        row.set_activatable_widget(widget)
    if isinstance(widget, Gtk.Scale):
        # A hard 220px minimum plus the label and reset action can prevent
        # Preferences from becoming narrow enough for compact navigation.
        # Let the slider grow on large windows but shrink on small ones.
        widget.set_size_request(110, -1)
        widget.set_hexpand(True)
    row.add_suffix(widget)
    group.add(row)
    return row


def append_action(group, title, button_title, callback, subtitle=None):
    button = Gtk.Button(label=button_title)
    button.connect("clicked", callback)
    row = action_row(group, title, button, subtitle)
    return row, button


def compact_status_labels(*labels):
    """Bound long service-state text to one line on narrow native ActionRows.

    Labels remain selectable and their owners expose the full text as a tooltip.
    """
    for indicator in labels:
        indicator.set_single_line_mode(True)
        indicator.set_max_width_chars(24)
        indicator.set_ellipsize(Pango.EllipsizeMode.END)


def set_status_labels(labels, values):
    """Preserve the complete status for selection and hover while showing compact text."""
    for label, value in zip(labels, values):
        label.set_text(value)
        label.set_tooltip_text(value)


class AdaptiveControlRow(Adw.PreferencesRow):
    """Native preference row with a full-width control in compact layouts.

    Ordinary ActionRows keep suffixes next to text at every width, making
    font selectors, color swatches and numeric reset actions squeeze labels.
    This remains an Adw.PreferencesRow in the boxed list and reflows its
    label/control boxes only at the Preferences window's breakpoint.
    """

    def __init__(self, title: str, subtitle: str = ""):
        super().__init__(title=title)
        # Controls always get a separate line. A horizontal minimum-size
        # control can keep the window wider than its adaptive breakpoint,
        # causing clipped suffixes even though resize handlers exist.
        self.layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.layout.set_margin_top(12)
        self.layout.set_margin_bottom(12)
        self.layout.set_margin_start(14)
        self.layout.set_margin_end(14)
        captions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3,
                           hexpand=True)
        self.title_label = Gtk.Label(label=title, xalign=0, wrap=True)
        self.title_label.add_css_class("heading")
        self.subtitle_label = Gtk.Label(label=subtitle, xalign=0, wrap=True)
        self.subtitle_label.add_css_class("dim-label")
        self.subtitle_label.set_visible(bool(subtitle))
        captions.append(self.title_label)
        captions.append(self.subtitle_label)
        self.suffix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.suffix_box.set_halign(Gtk.Align.FILL)
        self.suffix_box.set_hexpand(True)
        self.layout.append(captions)
        self.layout.append(self.suffix_box)
        self.layout.set_hexpand(True)
        self.set_child(self.layout)

    def add_suffix(self, widget):
        widget.set_valign(Gtk.Align.CENTER)
        self.suffix_box.append(widget)

    def set_subtitle(self, subtitle):
        self.subtitle_label.set_text(subtitle)
        self.subtitle_label.set_visible(bool(subtitle))

    def set_title(self, title):
        super().set_title(title)
        self.title_label.set_text(title)


def adaptive_action_row(group, title, widget, subtitle=None):
    row = AdaptiveControlRow(title, subtitle or "")
    if isinstance(widget, Gtk.Scale):
        widget.set_size_request(110, -1)
        widget.set_hexpand(True)
    row.add_suffix(widget)
    group.add(row)
    return row


def adaptive_append_action(group, title, button_title, callback, subtitle=None):
    """Navigation/action buttons below text, rather than clipped row suffixes."""
    button = Gtk.Button(label=button_title)
    button.connect("clicked", callback)
    row = adaptive_action_row(group, title, button, subtitle)
    return row, button


def center_string_dropdown(dropdown, minimum_width=155):
    """Fill each filter slot and center the visible and popup labels.

    GTK4 DropDown's standard string factory left-aligns both views, leaving
    excess space on wide filter rows. A list-item factory lets the selected
    label and every popup entry use the full allocated width. The model and
    selected indexes stay unchanged.
    """
    factory = Gtk.SignalListItemFactory()

    def setup(_factory, item):
        label = Gtk.Label(xalign=0.5, hexpand=True)
        label.set_halign(Gtk.Align.FILL)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        item.set_child(label)

    def bind(_factory, item):
        value = item.get_item()
        item.get_child().set_text(value.get_string() if isinstance(value, Gtk.StringObject) else '')

    factory.connect('setup', setup)
    factory.connect('bind', bind)
    dropdown.set_factory(factory)
    dropdown.set_list_factory(factory)
    dropdown.set_hexpand(True)
    dropdown.set_halign(Gtk.Align.FILL)
    dropdown.set_size_request(minimum_width, -1)
    return dropdown
