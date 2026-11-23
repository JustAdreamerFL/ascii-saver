"""Native Adwaita performance view with independent axes and per-display rows.

Five-minute process samples, not global compositor/GPU utilization. The
shared GTK/VTE process is deliberately never attributed to individual monitors.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib, Gdk, Adw
from window_shortcuts import install_close_shortcuts

from performance_series import make_series, metric_range
from performance_summary import summarize_performance


# Distinct line colors for simultaneous displays. Shared GTK/VTE uses a dashed
# gray line, so the legend remains interpretable without relying on hue alone.
LINE_COLORS = (
    (0.29, 0.70, 0.95), (1.0, 0.69, 0.32), (0.42, 0.80, 0.56),
    (0.84, 0.61, 0.98), (1.0, 0.50, 0.53), (0.45, 0.77, 0.79),
)
SHARED_COLOR = (0.65, 0.67, 0.73)
CHARTS = (
    ('CPU (% of one logical core)', 'cpu_percent'),
    ('Resident memory (MiB)', 'rss_mib'),
    ('GPU process-engine busy (%)', 'gpu_percent'),
    ('ttfx output FPS (completed effects)', 'active_output_fps'),
)


def _label(value, unit, precision=1):
    return 'n/a' if value is None else f'{value:.{precision}f} {unit}'


def _pretty_effect(effect):
    return str(effect).replace('_', ' ').title()


class PerformanceWindow(Adw.Window):
    def __init__(self, file_path):
        super().__init__(title='Screensaver Performance (last 5 minutes)')
        install_close_shortcuts(self, Gtk, Gdk)
        self.path = Path(file_path)
        self.set_default_size(940, 730)
        self.records = []
        self._closed = False
        self._last_monitor_ids = ()
        self._view_signature = None
        self._summary_rows = {}
        self._shared_row = None
        self._monitor_names = {}

        display = Gdk.Display.get_default()
        if display:
            monitors = display.get_monitors()
            for index in range(monitors.get_n_items()):
                monitor = monitors.get_item(index)
                connector = monitor.get_connector() or monitor.get_model()
                if connector:
                    self._monitor_names[connector] = (
                        f'Display {index + 1}: {monitor.get_model() or "Monitor"} ({connector})'
                    )

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        for margin in ('set_margin_top', 'set_margin_bottom', 'set_margin_start', 'set_margin_end'):
            getattr(outer, margin)(18)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(outer)

        selector_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        selector_row.append(Gtk.Label(label='Display', xalign=0))
        self.monitor_selector = Gtk.ComboBoxText()
        self.monitor_selector.append('all', 'All displays')
        self.monitor_selector.set_active_id('all')
        self.monitor_selector.set_hexpand(True)
        self.monitor_selector.connect('changed', self._change_monitor)
        selector_row.append(self.monitor_selector)
        outer.append(selector_row)

        charts = Adw.PreferencesGroup(title='Resource usage over time',
            description='Rolling five-minute window. Each metric has its own labeled vertical scale.')
        self.legend = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        charts.add(self.legend)
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_content_height(590)
        self.canvas.set_hexpand(True)
        self.canvas.set_draw_func(self.draw)
        charts.add(self.canvas)
        outer.append(charts)

        self.summary_groups = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.append(self.summary_groups)

        scope = Gtk.Label(xalign=0, wrap=True,
            label='CPU: 100% equals one fully busy logical core. RAM: process RSS, not a '
                  'de-duplicated total. GPU: DRM process-engine busy time (may exceed 100% '
                  'across engines), not whole-GPU utilization. FPS: ttfx output, not '
                  'frames presented by the compositor.')
        scope.add_css_class('dim-label')
        outer.append(scope)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(scroll)
        self.set_content(toolbar)
        self.connect('close-request', self._mark_closed)
        self.refresh()
        GLib.timeout_add_seconds(2, self.refresh)

    def _mark_closed(self, *_args):
        self._closed = True
        return False

    def _display_name(self, monitor):
        if monitor == '__shared__':
            return 'Shared GTK/VTE'
        if monitor == 'preview':
            return 'Preview'
        return self._monitor_names.get(monitor, monitor)

    def _change_monitor(self, _combo):
        self._update_view()

    def refresh(self):
        if self._closed:
            return GLib.SOURCE_REMOVE
        cutoff = time.time() - 300
        try:
            # Bounded reading; the saver rotates its JSONL log.
            lines = self.path.read_text(encoding='utf-8').splitlines()[-3000:]
        except (OSError, UnicodeError):
            lines = []
        records = []
        for line in lines:
            try:
                record = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(record, dict):
                continue
            timestamp = record.get('wall_timestamp')
            if type(timestamp) not in (int, float) or not cutoff <= timestamp <= time.time() + 5:
                continue
            records.append(record)
        self.records = records
        monitors = tuple(sorted({r['monitor'] for r in records
                                 if isinstance(r.get('monitor'), str) and r['monitor']}))
        if monitors != self._last_monitor_ids:
            selected = self.monitor_selector.get_active_id() or 'all'
            self.monitor_selector.remove_all()
            self.monitor_selector.append('all', 'All displays')
            for monitor in monitors:
                self.monitor_selector.append(monitor, self._display_name(monitor))
            self.monitor_selector.set_active_id(selected if selected in monitors else 'all')
            self._last_monitor_ids = monitors
        self._update_view()
        return GLib.SOURCE_CONTINUE

    def _filtered_records(self):
        selected = self.monitor_selector.get_active_id()
        if selected in (None, 'all'):
            return self.records
        return [r for r in self.records if r.get('monitor') == selected]

    def _line_color(self, monitor):
        if monitor == '__shared__':
            return SHARED_COLOR
        actual = [name for name in self._last_monitor_ids if name != '__shared__']
        return LINE_COLORS[actual.index(monitor) % len(LINE_COLORS)] if monitor in actual else LINE_COLORS[0]

    def _update_legend(self, monitors):
        while self.legend.get_first_child() is not None:
            self.legend.remove(self.legend.get_first_child())
        if not monitors:
            item = Gtk.Label(label='No samples yet. Start the screensaver to collect data.', xalign=0)
            item.add_css_class('dim-label')
            self.legend.append(item)
            return
        for monitor in monitors:
            color = self._line_color(monitor)
            hex_color = '#%02x%02x%02x' % tuple(round(channel * 255) for channel in color)
            marker = '┄┄' if monitor == '__shared__' else '●'
            label = Gtk.Label(xalign=0, selectable=False)
            label.set_markup(f'<span foreground="{hex_color}">{marker}</span>  '
                             + GLib.markup_escape_text(self._display_name(monitor)))
            self.legend.append(label)

    def _update_view(self):
        records = self._filtered_records()
        visible_monitors = tuple(sorted({r['monitor'] for r in records
                                         if isinstance(r.get('monitor'), str) and r['monitor']}))
        if getattr(self, '_legend_signature', None) != visible_monitors:
            self._legend_signature = visible_monitors
            self._update_legend(visible_monitors)
        grouped, shared = summarize_performance(records)
        signature = (tuple((monitor, tuple(r['effect'] for r in rows))
                           for monitor, rows in grouped.items()), bool(shared))
        if signature != self._view_signature:
            self._view_signature = signature
            self._rebuild_summary(grouped, shared)
        self._refresh_summary_values(grouped, shared)
        self.canvas.queue_draw()

    def _rebuild_summary(self, grouped, shared):
        while self.summary_groups.get_first_child() is not None:
            self.summary_groups.remove(self.summary_groups.get_first_child())
        self._summary_rows = {}
        self._shared_row = None
        if shared is not None:
            group = Adw.PreferencesGroup(title='Shared GTK/VTE process',
                description='Application rendering overhead is not attributable to any one display.')
            row = Adw.ActionRow(title='GTK/VTE renderer')
            row.set_subtitle_lines(0)
            row.set_subtitle_selectable(True)
            suffix = Gtk.Label(xalign=1)
            suffix.add_css_class('numeric')
            row.add_suffix(suffix)
            group.add(row)
            self._shared_row = (row, suffix)
            self.summary_groups.append(group)
        for monitor, effects in grouped.items():
            group = Adw.PreferencesGroup(title=self._display_name(monitor),
                description='Per-effect ttfx child process samples (not shared GTK/VTE costs).')
            for result in effects:
                row = Adw.ActionRow(title=_pretty_effect(result['effect']))
                row.set_subtitle_lines(0)
                row.set_subtitle_selectable(True)
                suffix = Gtk.Label(xalign=1)
                suffix.add_css_class('numeric')
                suffix.set_valign(Gtk.Align.CENTER)
                row.add_suffix(suffix)
                group.add(row)
                self._summary_rows[(monitor, result['effect'])] = (row, suffix)
            self.summary_groups.append(group)
        if not grouped and shared is None:
            empty = Adw.StatusPage(title='No performance samples yet',
                description='Run the screensaver to collect CPU, memory and renderer FPS readings.',
                icon_name='utilities-system-monitor-symbolic')
            self.summary_groups.append(empty)

    def _refresh_summary_values(self, grouped, shared):
        if self._shared_row and shared is not None:
            row, suffix = self._shared_row
            # Keep this explicit label: shared CPU is distinct from ttfx child CPU.
            row.set_subtitle('SHARED GTK/VTE: average CPU '
                + _label(shared['cpu'], '%') + ' · GPU engine ' + _label(shared['gpu'], '%')
                + f" · {shared['samples']} samples")
            suffix.set_text('Peak RSS: ' + _label(shared['rss'], 'MiB'))
        for monitor, results in grouped.items():
            for value in results:
                row, suffix = self._summary_rows[(monitor, value['effect'])]
                details = [f"Average CPU {_label(value['cpu'], '%')}",
                           f"GPU engine {_label(value['gpu'], '%')}",
                           f"Output FPS {_label(value['fps'], 'FPS')}"]
                if value['cap'] is not None:
                    details.append(f"configured cap {value['cap']:g} FPS")
                if value['duration'] is not None:
                    details.append(f"duration {value['duration']:.2f} s "
                                   f"({value['duration_runs']} completed runs, no final hold)")
                details.append(f"{value['samples']} CPU/RAM samples")
                row.set_subtitle(' · '.join(details))
                suffix.set_text('Peak RSS: ' + _label(value['rss'], 'MiB'))

    def draw(self, _widget, cr, width, height):
        dark = Adw.StyleManager.get_default().get_dark()
        background = (.13, .14, .17) if dark else (.97, .97, .98)
        foreground = (.91, .92, .95) if dark else (.15, .17, .22)
        grid = (.38, .40, .43) if dark else (.77, .79, .81)
        cr.set_source_rgb(*background)
        cr.paint()
        cr.select_font_face('Sans')
        cr.set_font_size(11)
        left, right = 67, max(width - 18, 68)
        now = time.time()
        plots_height = height / len(CHARTS)
        records = self._filtered_records()
        for index, (label, metric) in enumerate(CHARTS):
            panel_top = index * plots_height
            y_top, y_bottom = panel_top + 30, (index + 1) * plots_height - 25
            cr.set_source_rgb(*foreground)
            cr.move_to(12, panel_top + 17)
            cr.show_text(label)
            series_by_monitor = make_series(records, metric, now,
                monitor=self.monitor_selector.get_active_id())
            maximum = metric_range(series_by_monitor)
            cr.set_source_rgb(*grid)
            for fraction in (0, .5, 1):
                y = y_bottom - fraction * (y_bottom - y_top)
                value = maximum * fraction
                tick = f'{value:.1f}' if value < 10 else f'{value:.0f}'
                cr.move_to(14, y + 4)
                cr.show_text(tick)
                cr.move_to(left, y)
                cr.line_to(right, y)
                cr.stroke()
            if not series_by_monitor:
                cr.set_source_rgb(*foreground)
                cr.move_to(left + 12, y_top + 22)
                cr.show_text('No output FPS reports' if metric == 'active_output_fps'
                             else ('DRM counters unavailable' if metric == 'gpu_percent'
                                   else 'No samples'))
            for monitor, points in series_by_monitor.items():
                cr.set_source_rgb(*self._line_color(monitor))
                cr.set_line_width(1.8)
                cr.set_dash([5, 4] if monitor == '__shared__' else [])
                previous = None
                for timestamp, value in points:
                    x = max(left, min(right, left + (timestamp - (now - 300)) / 300 * (right - left)))
                    y = y_bottom - value / maximum * (y_bottom - y_top)
                    if metric == 'active_output_fps':
                        # Per-effect FPS is an event, not a continuous sample.
                        cr.arc(x, y, 2.8, 0, 6.283185307179586)
                        cr.fill()
                    else:
                        if previous is None or timestamp - previous[0] > 15:
                            # Also render isolated points that cannot form a line.
                            cr.arc(x, y, 2.1, 0, 6.283185307179586)
                            cr.fill()
                            cr.move_to(x, y)
                        else:
                            cr.line_to(x, y)
                            cr.stroke()
                            cr.move_to(x, y)
                    previous = (timestamp, value)
                cr.set_dash([])
            if index == len(CHARTS) - 1:
                cr.set_source_rgb(*foreground)
                for fraction, text in ((0, '−5 min'), (.5, '−2.5 min'), (1, 'Now')):
                    cr.move_to(left + fraction * (right - left) - (7 if fraction else 0),
                               height - 5)
                    cr.show_text(text)
