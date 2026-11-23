"""GNOME HIG primary menu, help, keyboard shortcuts and component details.

The module owns auxiliary windows and keeps the dashboard/settings independent
from the implementation of About and diagnostics dialogs.
"""
from __future__ import annotations

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, Pango, Gdk

from build_info import BUILD_VERSION
from component_versions import collect_versions, troubleshooting_report


SHORTCUTS = (
    ('Preferences', '<Primary>comma'),
    ('Keyboard Shortcuts', '<Primary>question'),
    ('Help', 'F1'),
    ('Main Menu', 'F10'),
    ('Close Window', '<Primary>w'),
    ('Quit', '<Primary>q'),
)


def primary_menu() -> Gio.Menu:
    menu = Gio.Menu()
    system = Gio.Menu()
    system.append('System Information', 'app.components')
    menu.append_section(None, system)
    # Tools are available together on the Preferences > Tools page.
    standard = Gio.Menu()
    standard.append('Preferences', 'app.preferences')
    standard.append('Keyboard Shortcuts', 'app.shortcuts')
    standard.append('Help', 'app.help')
    standard.append('About ASCII Saver', 'app.about')
    menu.append_section(None, standard)
    session = Gio.Menu()
    session.append('Quit', 'app.quit')
    menu.append_section(None, session)
    return menu


def new_main_menu_button() -> Gtk.MenuButton:
    button = Gtk.MenuButton(icon_name='open-menu-symbolic')
    button.set_tooltip_text('Main Menu')
    button.set_menu_model(primary_menu())
    return button


def _window(parent, title: str, width: int = 580, height: int = 480):
    # These are application dialogs, not independent non-modal windows.
    # Esc works on both GNOME and KDE even if the compositor does not
    # provide a close titlebar button for the transient window.
    win = Adw.Window(title=title, transient_for=parent, modal=True)
    win.set_default_size(width, height)
    key_controller = Gtk.EventControllerKey()
    def on_key_pressed(_controller, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape:
            win.close()
            return True
        return False
    key_controller.connect('key-pressed', on_key_pressed)
    win.add_controller(key_controller)
    toolbar = Adw.ToolbarView()
    header = Adw.HeaderBar()
    # Adw.HeaderBar already adds the standard close button to modal windows.
    # Do not pack another Close button alongside it. Escape is handled above.
    toolbar.add_top_bar(header)
    page = Adw.PreferencesPage()
    scroller = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
    scroller.set_child(page)
    toolbar.set_content(scroller)
    win.set_content(toolbar)
    return win, page, header


def _row(group, title: str, subtitle: str, value: str | None = None):
    row = Adw.ActionRow(title=title, subtitle=subtitle)
    if value is not None:
        label = Gtk.Label(label=value, selectable=True, xalign=1)
        label.add_css_class('dim-label')
        label.set_ellipsize(Pango.EllipsizeMode.END)
        row.add_suffix(label)
    group.add(row)
    return row


def show_components(parent):
    win, page, header = _window(parent, 'System Information')
    group = Adw.PreferencesGroup(title='Installed components', description='Versions and whether the running watcher matches the installed build.')
    ui = _row(group, 'Application', 'Running graphical interface')
    package = _row(group, 'Installed release', 'Files currently installed on disk')
    ui_status = _row(group, 'GUI status', 'Whether the running interface matches the installed release')
    renderer = _row(group, 'Animation engine', 'Bundled Rust ttfx renderer')
    watcher = _row(group, 'Idle watcher', 'Native background service')
    backend = _row(group, 'Desktop integration', 'Detected watcher backend')
    status = _row(group, 'Watcher status', 'Checks the actual running executable, not just the PID file')
    page.add(group)
    session_group = Adw.PreferencesGroup(title='Environment')
    session = _row(session_group, 'Desktop session', 'Active session reported by the system')
    page.add(session_group)
    labels = {'ui': ui, 'installed': package, 'ui_status': ui_status, 'renderer': renderer,
              'watcher': watcher, 'backend': backend, 'running': status,
              'session': session}

    def refresh(*_args):
        versions = collect_versions()
        for key, row in labels.items():
            row.set_subtitle(str(versions[key]))
        if 'Restart required' in versions['running']:
            status.add_css_class('warning')
        else:
            status.remove_css_class('warning')

    button = Gtk.Button(icon_name='view-refresh-symbolic', tooltip_text='Refresh component status')
    button.connect('clicked', refresh)
    header.pack_end(button)
    refresh()
    win.present()
    return win


def show_about(parent):
    versions = collect_versions()
    if hasattr(Adw, 'AboutDialog'):
        dialog = Adw.AboutDialog()
        dialog.set_application_name('ASCII Saver')
        dialog.set_application_icon('com.github.justadreamerfl.asciisaver')
        dialog.set_version(BUILD_VERSION)
        dialog.set_comments('Terminal-effect screensaver for GNOME and KDE Plasma.')
        dialog.set_debug_info(troubleshooting_report(versions))
        dialog.set_debug_info_filename('ascii-saver-components.txt')
        dialog.present(parent)
        return dialog
    dialog = Gtk.AboutDialog(transient_for=parent, modal=True)
    dialog.set_program_name('ASCII Saver')
    dialog.set_version(BUILD_VERSION)
    dialog.set_comments('Terminal-effect screensaver for GNOME and KDE Plasma.\n\n' + troubleshooting_report(versions))
    dialog.present()
    return dialog


def show_shortcuts(parent):
    if hasattr(Adw, 'ShortcutsDialog'):
        dialog = Adw.ShortcutsDialog()
        section = Adw.ShortcutsSection.new('General')
        for label, accel in SHORTCUTS:
            section.add(Adw.ShortcutsItem.new(label, accel))
        dialog.add(section)
        dialog.present(parent)
        return dialog
    win, page, _header = _window(parent, 'Keyboard Shortcuts')
    group = Adw.PreferencesGroup(title='General')
    for label, accel in SHORTCUTS:
        row = Adw.ActionRow(title=label)
        row.add_suffix(Gtk.ShortcutLabel(accelerator=accel))
        group.add(row)
    page.add(group)
    win.present()
    return win


def show_help(parent):
    win, page, _header = _window(parent, 'Help')
    groups = (
        ('Getting started', (
            ('Start Now', 'Launches the fullscreen screensaver. Move the mouse or press a key to dismiss it.'),
            ('Preview', 'Opens a persistent, resizable window that plays the full effect sequence.'),
            ('Preferences', 'Adjust activation, appearance, displays, animations and preview settings.'),
        )),
        ('Explore', (
            ('Effect Library', 'Browse all effects, enable or disable them, and preview an individual effect.'),
            ('Playlist Editor', 'Choose which effects run and in what order.'),
            ('System Information', 'Compare the installed and running application components after an upgrade.'),
        )),
    )
    for title, rows in groups:
        group = Adw.PreferencesGroup(title=title)
        for row_title, description in rows:
            _row(group, row_title, description)
        page.add(group)
    win.present()
    return win
