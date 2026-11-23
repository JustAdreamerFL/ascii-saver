"""Generate editable stage playlists from empirical duration groups.

Durations are *relative* to the set measured on this user's installation.
Intensity remains a qualitative tag. Lack of samples fails visibly rather
than silently reverting to potentially misleading guessed duration values.
"""
from __future__ import annotations
from pathlib import Path
import random
from effect_profiles import read_records, profile
from playlist_engine import EFFECTS, group, validate
from auto_playlists import PATTERNS

def generate_from_measurements(cache_folder, pattern, duration='any', per_stage=4,
                               excluded=(), monitor=None, seed=None, min_runs=3):
    if pattern not in PATTERNS:
        raise ValueError('Unknown energy pattern')
    if duration not in ('any','short','medium','long'):
        raise ValueError('Unknown duration category')
    if type(per_stage) is not int or not 1 <= per_stage <= 20:
        raise ValueError('Effects per stage must be 1–20')
    if duration == 'any':
        raise ValueError('Select Short, Medium, or Long to use measured duration grouping')
    rows=profile(read_records(Path(cache_folder)), min_runs=min_runs)
    # Multiple monitors: use the slowest observed relative class when grouping,
    # never pick a specific display by accidental iteration ordering.
    tiers={'short':0,'medium':1,'long':2}
    allowed={}
    for row in rows:
        if monitor is not None and row['monitor']!=monitor:
            continue
        effect=row['effect']; category=row['relative_duration']
        if effect in EFFECTS:
            allowed[effect]=max(allowed.get(effect,0), tiers[category])
    if not allowed:
        raise ValueError('Not enough measurements yet. Run at least three successful cycles of several effects.')
    target=tiers[duration]
    rng=random.Random(seed)
    result=[]
    for i,energy in enumerate(PATTERNS[pattern],1):
        matches=[name for name,rank in allowed.items()
                 if rank==target and name not in excluded and group(name)['intensity']==energy]
        if not matches:
            raise ValueError(f'No measured {duration} effects match {energy}. Run more effects or choose another duration.')
        rng.shuffle(matches)
        result.append({'name':f'{i:02d} · {energy.title()} · {duration.title()}',
                       'enabled':True,'order':'sequential',
                       'effects':matches[:per_stage]})
    return validate(result)
