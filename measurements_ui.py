"""Grouped, filterable empirical duration measurements in native Adwaita rows."""
from __future__ import annotations
from collections import defaultdict


def group_measurements(records):
    groups = defaultdict(list)
    for item in records:
        if item.get('monitor') and item.get('effect'):
            groups[str(item['monitor'])].append(item)
    return dict(sorted(groups.items(), key=lambda p: (p[0] == 'preview', p[0])))


def display_name(connector: str, monitor_names: dict[str, str]) -> str:
    if connector == 'preview':
        return 'Preview'
    name = monitor_names.get(connector)
    if name and name != connector:
        return f'{name} ({connector})'
    return connector


def build_window(parent, records, names=None):
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, Gdk
    from window_shortcuts import install_close_shortcuts
    names = names or {}
    window = Adw.Window(title='Measured effect durations', transient_for=parent)
    install_close_shortcuts(window, Gtk, Gdk)
    window.set_default_size(810, 650)
    toolbar = Adw.ToolbarView()
    toolbar.add_top_bar(Adw.HeaderBar())
    groups = group_measurements(records)
    if not groups:
        page = Adw.StatusPage(title='No measurements yet',
            description='Complete an animation to record its duration for each display.',
            icon_name='document-open-recent-symbolic')
        toolbar.set_content(page)
    else:
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        picker_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        picker_row.set_margin_top(12)
        picker_row.set_margin_start(24)
        picker_row.set_margin_end(24)
        picker_label = Gtk.Label(label='Display', xalign=0)
        picker = Gtk.DropDown.new_from_strings(['All displays'] + [display_name(k, names) for k in groups])
        picker.set_hexpand(True)
        picker_row.append(picker_label)
        picker_row.append(picker)
        content.append(picker_row)
        page = Adw.PreferencesPage()
        group_widgets = []
        for monitor, results in groups.items():
            group = Adw.PreferencesGroup(title=display_name(monitor, names))
            group.set_description(
                f'{len(results)} measured effects · {sum(int(r["runs"]) for r in results)} completed runs · '
                'durations exclude the final artwork hold; short/medium/long is relative to this display'
            )
            for result in sorted(results, key=lambda x: x['effect']):
                runs = result['runs']
                subtitle = (f'{runs} run(s) · min {result["minimum_seconds"]:.2f} s · '
                            f'max {result["maximum_seconds"]:.2f} s · '
                            f'{result["relative_duration"]} duration')
                if runs < 3:
                    subtitle += ' · preliminary'
                row = Adw.ActionRow(title=result['effect'].replace('_',' ').title(), subtitle=subtitle)
                row.set_subtitle_lines(0)
                number = Gtk.Label(label=f'Median {result["median_seconds"]:.2f} s')
                number.add_css_class('numeric')
                number.set_valign(Gtk.Align.CENTER)
                row.add_suffix(number)
                group.add(row)
            page.add(group)
            group_widgets.append(group)
        picker.connect('notify::selected', lambda dropdown, *_: [
            g.set_visible(dropdown.get_selected() in (0, index))
            for index, g in enumerate(group_widgets, start=1)])
        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(page)
        content.append(scroller)
        toolbar.set_content(content)
    window.set_content(toolbar)
    return window
