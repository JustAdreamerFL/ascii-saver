"""Generate editable energy-curve playlists using qualitative effect metadata.

No duration/intensity claims here are based on measured benchmarks. This is a
starting point for user curation, not a guarantee of actual effect behavior.
"""
from __future__ import annotations
import random
from playlist_engine import EFFECTS, group, validate

ENERGIES = ('gentle', 'moderate', 'energetic')
PATTERNS = {
    'Smooth wave': ('gentle', 'moderate', 'energetic', 'moderate', 'gentle'),
    'Calm → build → peak → cooldown': ('gentle', 'moderate', 'energetic', 'moderate'),
    'High energy with rests': ('energetic', 'energetic', 'gentle', 'energetic', 'gentle'),
    'Always calm': ('gentle',),
    'Always energetic': ('energetic',),
    'Alternating': ('gentle', 'energetic'),
}

def generate(pattern='Smooth wave', duration='any', per_stage=4, seed=None, excluded=()):
    if pattern not in PATTERNS:
        raise ValueError('Unknown energy pattern')
    if duration not in ('any','short','medium','long'):
        raise ValueError('Unknown duration preference')
    if type(per_stage) is not int or not 1 <= per_stage <= 20:
        raise ValueError('Number of effects per stage must be 1–20')
    rng=random.Random(seed)
    excluded=set(excluded)
    result=[]
    for index, energy in enumerate(PATTERNS[pattern], 1):
        candidates=[e for e in EFFECTS if e not in excluded and group(e)['intensity']==energy and (duration=='any' or group(e)['duration']==duration)]
        # Prefer chosen duration; fall back to same energy rather than creating empty stages.
        if not candidates:
            candidates=[e for e in EFFECTS if e not in excluded and group(e)['intensity']==energy]
        if not candidates:
            raise ValueError(f'No enabled effects available for {energy} stage')
        rng.shuffle(candidates)
        effects=candidates[:min(per_stage,len(candidates))]
        result.append({'name':f'{index:02d} · {energy.title()}', 'enabled':True, 'order':'sequential', 'effects':effects})
    return validate(result)
