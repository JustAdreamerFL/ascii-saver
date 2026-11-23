"""Offline empirical effect profiles from locally recorded animation durations."""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from statistics import median


def read_records(folder):
    folder=Path(folder)
    for filename in ('performance.jsonl.1','performance.jsonl'):
        path=folder/filename
        try:
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    try:
                        item=json.loads(line)
                    except (ValueError,UnicodeDecodeError):
                        continue
                    if isinstance(item,dict):
                        yield item
        except FileNotFoundError:
            continue


def profile(records,min_runs=3):
    """Median wall time by effect and monitor; unknown/failed runs excluded.

    Classifications are *relative to the current measured effects*, not fixed
    duration thresholds. Missing data remains unclassified.
    """
    samples=defaultdict(list)
    for record in records:
        if record.get('event')!='effect_duration' or record.get('success') is not True:
            continue
        effect=record.get('effect'); monitor=record.get('monitor')
        duration=record.get('duration_seconds')
        if not isinstance(effect,str) or effect in ('random','unknown') or not effect:
            continue
        if not isinstance(monitor,str) or not monitor:
            continue
        if type(duration) not in (int,float) or not (0 <= duration < 86400):
            continue
        samples[(monitor,effect)].append(duration)
    result=[]
    for (monitor,effect),values in sorted(samples.items()):
        if len(values)<min_runs:
            continue
        result.append({'monitor':monitor,'effect':effect,'runs':len(values),
                       'median_seconds':round(median(values),3),
                       'minimum_seconds':round(min(values),3),
                       'maximum_seconds':round(max(values),3)})
    for monitor in {r['monitor'] for r in result}:
        rows=sorted((r for r in result if r['monitor']==monitor),key=lambda r:r['median_seconds'])
        n=len(rows)
        for rank,row in enumerate(rows):
            # Rank by observed runtime within this monitor; ties are grouped
            # by stable sorted order. Not a measure of perceptual dynamics.
            row['relative_duration']=('short' if rank < n/3 else 'medium' if rank < 2*n/3 else 'long')
    return result


def recommend_groups(rows, monitor=None):
    """Suggest candidates for three user-editable playlists, never overwrite."""
    selected=[r for r in rows if monitor is None or r['monitor']==monitor]
    output={'short':[], 'medium':[], 'long':[]}
    for row in selected:
        group=row['relative_duration']
        if row['effect'] not in output[group]:
            output[group].append(row['effect'])
    return output
