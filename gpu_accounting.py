"""Linux DRM fdinfo process-engine accounting.

DRM GPU engine counters measure scheduled GPU engine busy time, not GPU chip
utilization. Values are per process and engine, when the driver implements
DRM fdinfo. Compositor GPU usage is outside this process and not attributed.
No DRM fdinfo => no measurement (never manufacture zero).
"""
from __future__ import annotations
from pathlib import Path
import re

LINE = re.compile(r"^drm-engine-([A-Za-z0-9_-]+):\s*([0-9]+)\s*ns\s*$")

def read_engine_counters(pid: int, proc_root: Path = Path('/proc')) -> dict[str,int] | None:
    fdroot = Path(proc_root) / str(pid) / 'fdinfo'
    try:
        files = list(fdroot.iterdir())
    except OSError:
        return None
    # Track handles by physical GPU / client ID where possible. Duplicated
    # file descriptors referring to the same DRM client must not double-count.
    clients: dict[tuple[str,str], dict[str,int]] = {}
    for fdinfo in files:
        try:
            lines = fdinfo.read_text(encoding='utf-8',errors='replace').splitlines()
        except OSError:
            continue
        fields = dict(line.split(':',1) for line in lines if ':' in line)
        drm_driver = fields.get('drm-driver', '').strip()
        client = fields.get('drm-client-id', '').strip()
        pdev = fields.get('drm-pdev', '').strip()
        counts={}
        for line in lines:
            match=LINE.fullmatch(line)
            if match:
                counts[match.group(1)] = int(match.group(2))
        if not counts:
            continue
        # fdinfo for the same DRM client may appear at multiple fds. If the
        # driver lacks client id we can't safely aggregate, so skip it.
        if not client:
            continue
        identity=(f'{drm_driver}:{pdev}', client)
        previous=clients.setdefault(identity,{})
        for name,val in counts.items():
            previous[name]=max(previous.get(name,0),val)
    if not clients:
        return None
    totals={}
    for counter in clients.values():
        for name,ns in counter.items():
            totals[name] = totals.get(name,0)+ns
    return totals

class GPUSampler:
    def __init__(self,proc_root: Path=Path('/proc')):
        self.proc_root=Path(proc_root)
        self.previous={}

    def sample(self,pid:int, process_birth:int, now:float) -> dict[str,float] | None:
        counts=read_engine_counters(pid,self.proc_root)
        if not counts:
            self.previous.pop(pid,None)
            return None
        old=self.previous.get(pid)
        self.previous[pid]=(process_birth,now,counts)
        if old is None or old[0]!=process_birth or now<=old[1]:
            return None
        elapsed_ns=(now-old[1])*1e9
        result={}
        for name,counter in counts.items():
            previous=old[2].get(name)
            if previous is not None and counter>=previous:
                result[name]=round(100*(counter-previous)/elapsed_ns,2)
        return result or None
