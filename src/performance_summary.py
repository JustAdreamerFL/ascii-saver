"""Per-display performance summaries for the diagnostics UI.

Only ttfx child process samples are attributed to a display. The GUI/VTE
process is reported separately to prevent misleading per-monitor totals.
Metrics without valid samples are represented as None, never as zero.
"""
from __future__ import annotations

from collections import defaultdict
from math import isfinite


def _number(value):
    if type(value) not in (float, int) or not isfinite(value) or value < 0:
        return None
    return float(value)


def _average(values):
    return sum(values) / len(values) if values else None


def summarize_performance(records):
    """Return (per_monitor, shared) from rolling JSONL performance records.

    Per-monitor values are grouped by effect. `fps` comes exclusively from
    frame_stats and `cap` from effect_start. Durations exclude artwork holds.
    """
    data = defaultdict(lambda: {
        'cpu': [], 'rss': [], 'gpu': [], 'fps': [], 'duration': [],
        'cap': None, 'samples': 0,
    })
    shared = {'cpu': [], 'rss': [], 'gpu': [], 'samples': 0}
    for record in records:
        if not isinstance(record, dict):
            continue
        monitor = record.get('monitor')
        effect = record.get('effect')
        event = record.get('event')
        if monitor == '__shared__':
            if event != 'shared_process_sample':
                continue
            target = shared
        else:
            if not isinstance(monitor, str) or not monitor or not isinstance(effect, str) or not effect:
                continue
            target = data[(monitor, effect)]
        if event == 'frame_stats' and target is not shared:
            number = _number(record.get('active_output_fps'))
            if number is not None:
                target['fps'].append(number)
        elif event == 'effect_start' and target is not shared:
            number = _number(record.get('fps_cap'))
            if number is not None:
                target['cap'] = number
        elif event == 'effect_duration' and target is not shared:
            if record.get('success') is True:
                number = _number(record.get('duration_seconds'))
                if number is not None and number < 86400:
                    target['duration'].append(number)
        elif event in ('shared_process_sample', None, 'process_sample'):
            # No shared-process data may appear under an individual monitor.
            if (target is shared) != (event == 'shared_process_sample'):
                continue
            has_metric = False
            for key, field in (('cpu', 'cpu_percent'), ('rss', 'rss_mib'), ('gpu', 'gpu_percent')):
                number = _number(record.get(field))
                if number is not None:
                    target[key].append(number)
                    has_metric = True
            if has_metric:
                target['samples'] += 1

    grouped = defaultdict(list)
    for (monitor, effect), values in sorted(data.items()):
        if not any((values['samples'], values['fps'], values['duration'], values['cap'] is not None)):
            continue
        grouped[monitor].append({
            'effect': effect,
            'samples': values['samples'],
            'cpu': _average(values['cpu']),
            'rss': max(values['rss']) if values['rss'] else None,
            'gpu': _average(values['gpu']),
            'fps': _average(values['fps']),
            'fps_runs': len(values['fps']),
            'cap': values['cap'],
            'duration': _average(values['duration']),
            'duration_runs': len(values['duration']),
        })
    shared_result = None
    if shared['samples']:
        shared_result = {
            'samples': shared['samples'],
            'cpu': _average(shared['cpu']),
            'rss': max(shared['rss']) if shared['rss'] else None,
            'gpu': _average(shared['gpu']),
        }
    return dict(grouped), shared_result
