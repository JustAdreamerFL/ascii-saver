"""Pure functions for the five-minute performance charts.

A DRM engine busy value is scheduled engine time / wall-clock time. It is
not whole-GPU utilization and may exceed 100% across parallel engines.
"""
from __future__ import annotations
import math
from collections import defaultdict

METRICS = ('cpu_percent', 'rss_mib', 'gpu_percent', 'active_output_fps')
SKIP_EVENTS = {'effect_start', 'effect_duration', 'effect_spawn_failed'}

def make_series(records, metric, now, seconds=300, monitor=None):
    if metric not in METRICS:
        raise ValueError(f'unsupported metric: {metric}')
    if seconds <= 0:
        raise ValueError('seconds must be positive')
    grouped = defaultdict(list)
    for record in records:
        if not isinstance(record, dict) or record.get('event') in SKIP_EVENTS:
            continue
        label = record.get('monitor')
        if not isinstance(label, str):
            continue
        if monitor not in (None, 'all') and label != monitor:
            continue
        if metric == 'active_output_fps' and record.get('event') != 'frame_stats':
            continue
        if metric != 'active_output_fps' and record.get('event') == 'frame_stats':
            continue
        value = record.get(metric)
        timestamp = record.get('wall_timestamp')
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not isinstance(timestamp, (int, float))
                or not math.isfinite(value) or not math.isfinite(timestamp)
                or timestamp < now-seconds or timestamp > now+5 or value < 0):
            continue
        grouped[label].append((float(timestamp), float(value)))
    return {label: sorted(points) for label, points in sorted(grouped.items())}

def metric_range(series):
    """Independent scale for each chart, allowing >100% multi-engine values."""
    highest = max((v for points in series.values() for _,v in points), default=0.0)
    return max(1.0, highest*1.15)
