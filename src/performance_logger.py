"""Low-overhead Linux /proc sampler for per-effect ttfx child processes.

Does not falsely attribute shared GTK/VTE GPU and CPU rendering overhead to
individual displays. Sampling stops once the child exits.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from gpu_accounting import GPUSampler
import json
import os
import time

HZ = os.sysconf('SC_CLK_TCK')
PAGE = os.sysconf('SC_PAGE_SIZE')


def read_proc(pid: int, proc_root: Path = Path('/proc')):
    try:
        stat = (proc_root / str(pid) / 'stat').read_text()
        # comm can contain spaces and parentheses. Parse after LAST ')'.
        data = stat.rsplit(')', 1)[1].split()
        cpu_ticks = int(data[11]) + int(data[12])
        rss_bytes = int(data[21]) * PAGE
        start_ticks = int(data[19])
        return cpu_ticks, rss_bytes, start_ticks
    except (OSError, ValueError, IndexError):
        return None


@dataclass
class Sample:
    timestamp: float
    pid: int
    monitor: str
    effect: str
    cpu_percent: float | None
    rss_mib: float
    gpu_percent: float | None = None  # Sum of available DRM engine busy-time ratios, NOT chip utilization.
    gpu_engines: dict | None = None
    fps: None = None  # Requires renderer/VTE instrumentation.

    def asdict(self):
        return dict(timestamp=self.timestamp, pid=self.pid, monitor=self.monitor,
                    effect=self.effect, cpu_percent=self.cpu_percent,
                    rss_mib=self.rss_mib, gpu_percent=self.gpu_percent,
                    gpu_engines=self.gpu_engines, fps=self.fps)


class ProcessSampler:
    def __init__(self, window_seconds=300, proc_root=Path('/proc')):
        self.window_seconds = window_seconds
        self.proc_root = Path(proc_root)
        self.previous = {}
        self.gpu = GPUSampler(self.proc_root)
        self.samples = deque()

    def sample(self, pid, monitor, effect, now=None):
        now = time.monotonic() if now is None else now
        proc = read_proc(pid, self.proc_root)
        if proc is None:
            self.previous.pop(pid, None)
            return None
        ticks, rss, birth = proc
        old = self.previous.get(pid)
        cpu = None
        if old and birth == old[0] and now > old[1]:
            cpu = max(0.0, 100.0 * (ticks - old[2]) / HZ / (now-old[1]))
        self.previous[pid] = (birth, now, ticks)
        engine_busy = self.gpu.sample(pid, birth, now)
        s = Sample(now, pid, monitor, effect, cpu, rss/1048576,
                   sum(engine_busy.values()) if engine_busy is not None else None, engine_busy)
        self.samples.append(s)
        cutoff = now - self.window_seconds
        while self.samples and self.samples[0].timestamp < cutoff:
            self.samples.popleft()
        return s

    def summarize(self):
        buckets = {}
        for s in self.samples:
            key = (s.monitor, s.effect)
            b = buckets.setdefault(key, {'monitor':s.monitor, 'effect':s.effect,
                'samples':0, 'cpu_sum':0.0, 'cpu_count':0, 'peak_rss_mib':0.0,
                'gpu_sum':0.0, 'gpu_count':0})
            b['samples'] += 1
            b['peak_rss_mib'] = max(b['peak_rss_mib'],s.rss_mib)
            if s.gpu_percent is not None:
                b['gpu_sum'] += s.gpu_percent
                b['gpu_count'] += 1
            if s.cpu_percent is not None:
                b['cpu_sum'] += s.cpu_percent
                b['cpu_count'] += 1
        return [dict(monitor=b['monitor'], effect=b['effect'], samples=b['samples'],
                     avg_cpu_percent=round(b['cpu_sum']/b['cpu_count'], 2) if b['cpu_count'] else None,
                     peak_rss_mib=round(b['peak_rss_mib'],2),
                     avg_gpu_engine_busy=round(b['gpu_sum']/b['gpu_count'],2) if b['gpu_count'] else None) for b in buckets.values()]


class JsonlRecorder:
    """Appends bounded data via externally configured cache path; no telemetry upload."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, sample: Sample):
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(sample.asdict(), separators=(',', ':'))+'\n')


def history(path, seconds=300):
    cutoff = time.time() - seconds
    records=[]
    try:
        with Path(path).open(encoding='utf-8') as f:
            for line in f:
                try:
                    d=json.loads(line)
                except ValueError:
                    continue
                if d.get('wall_timestamp', 0) >= cutoff:
                    records.append(d)
    except OSError:
        pass
    return records
