"""Local effect-duration records and bounded append-only JSONL writer."""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

class BoundedLog:
    def __init__(self, path, limit_bytes=5_000_000):
        self.path = Path(path)
        self.limit_bytes = limit_bytes
    def append(self, event):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Rename is atomic on a single filesystem; only the saver writes this log.
        try:
            if self.path.stat().st_size >= self.limit_bytes:
                self.path.replace(self.path.with_suffix(self.path.suffix + '.1'))
        except FileNotFoundError:
            pass
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(event, separators=(',', ':'))+'\n')

def duration_summaries(records):
    """Per-monitor/effect observed durations; exclude aborted and random effect names."""
    data={}
    for r in records:
        if r.get('event') != 'effect_duration' or r.get('success') is not True:
            continue
        seconds=r.get('duration_seconds')
        if not isinstance(seconds,(int,float)) or not 0 <= seconds < 86400:
            continue
        effect=r.get('effect')
        if not effect or effect == 'random':
            continue
        key=(str(r.get('monitor','?')),str(effect))
        data.setdefault(key,[]).append(seconds)
    return [{'monitor':m,'effect':e,'runs':len(v),
             'avg_seconds':round(sum(v)/len(v),2),
             'min_seconds':round(min(v),2),'max_seconds':round(max(v),2)}
            for (m,e),v in sorted(data.items())]
