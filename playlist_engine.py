"""Playlist planning for the ASCII Saver ttfx renderer.

Duration/speed groups are qualitative recommendations, not claims about measured
wall-clock duration. Real duration depends on input art and effect parameters.
"""
from __future__ import annotations
import random

EFFECTS = ("beams binarypath blackhole bouncyballs bubbles burn colorshift "
           "crumble decrypt errorcorrect expand fireworks highlight laseretch "
           "matrix middleout orbittingvolley overflow pour print rain "
           "randomsequence rings scattered slice slide smoke spotlights spray "
           "swarm sweep synthgrid thunderstorm unstable vhstape waves wipe").split()

# Editable qualitative metadata. Only used for organization, not as measured data.
INTENSITY = {
    "gentle": ["colorshift", "highlight", "print", "rain", "waves", "spotlights",
               "sweep", "wipe", "laseretch", "slide", "middleout"],
    "energetic": ["bouncyballs", "fireworks", "matrix", "swarm", "thunderstorm",
                  "rings", "blackhole", "unstable", "synthgrid", "orbittingvolley"],
}
DURATION = {
    "short": ["wipe", "slice", "slide", "sweep", "print", "decrypt",
              "randomsequence", "spray"],
    "long": ["matrix", "thunderstorm", "waves", "spotlights", "swarm",
             "rings", "colorshift", "orbittingvolley"],
}
DEFAULT_PLAYLISTS = [
    {"name":"Calm", "enabled":True, "order":"sequential", "effects":["colorshift","rain","waves","highlight"]},
    {"name":"Build", "enabled":True, "order":"sequential", "effects":["decrypt","beams","rings","synthgrid"]},
    {"name":"Peak", "enabled":True, "order":"sequential", "effects":["matrix","fireworks","swarm","unstable"]},
    {"name":"Cooldown", "enabled":True, "order":"sequential", "effects":["sweep","print","slide","wipe"]},
]

def group(effect):
    return {"intensity": ("gentle" if effect in INTENSITY["gentle"] else
                           "energetic" if effect in INTENSITY["energetic"] else "moderate"),
            "duration": ("short" if effect in DURATION["short"] else
                         "long" if effect in DURATION["long"] else "medium")}

def validate(playlists):
    if not isinstance(playlists, list) or len(playlists)>100:
        raise ValueError("playlists must be a list with at most 100 entries")
    result=[]
    for item in playlists:
        if not isinstance(item, dict):
            raise ValueError("playlist entries must be objects")
        name=item.get("name")
        effects=item.get("effects")
        order=item.get("order","sequential")
        if not isinstance(name,str) or not name.strip() or len(name)>80:
            raise ValueError("each playlist needs a nonempty name (max 80 chars)")
        if type(item.get("enabled", True)) is not bool:
            raise ValueError("enabled must be a boolean")
        if order not in ("sequential","shuffle"):
            raise ValueError("order must be sequential or shuffle")
        if not isinstance(effects,list) or not effects or any(e not in EFFECTS for e in effects):
            raise ValueError(f"{name}: add at least one recognized effect")
        result.append({"name":name.strip(),"enabled":item.get("enabled",True),
                       "order":order,"effects":list(effects)})
    return result

class Scheduler:
    def __init__(self, playlists, excluded=(), seed=None):
        self.playlists=[p for p in validate(playlists) if p["enabled"]]
        self.excluded=set(excluded)
        self.random=random.Random(seed)
        self.position=0
        self.indices=[0]*len(self.playlists)
        self.shuffled=[[] for p in self.playlists]
        self.last_shuffled=[None]*len(self.playlists)
    def next(self):
        if not self.playlists:
            return None
        for _ in range(len(self.playlists)):
            index=self.position%len(self.playlists)
            p=self.playlists[index]
            eligible=[e for e in p["effects"] if e not in self.excluded]
            if eligible:
                if p["order"]=="shuffle":
                    if not self.shuffled[index]:
                        self.shuffled[index]=eligible[:]
                        self.random.shuffle(self.shuffled[index])
                        # The first item popped from the new bag must not be
                        # the final item from the previous cycle, when there
                        # is an alternative. Avoid a boundary repeat.
                        if len(self.shuffled[index]) > 1 and self.shuffled[index][-1] == self.last_shuffled[index]:
                            alternate = next((i for i, name in enumerate(self.shuffled[index][:-1])
                                              if name != self.last_shuffled[index]), None)
                            if alternate is not None:
                                self.shuffled[index][-1], self.shuffled[index][alternate] = (
                                    self.shuffled[index][alternate], self.shuffled[index][-1])
                    effect=self.shuffled[index].pop()
                    self.last_shuffled[index]=effect
                else:
                    effect=eligible[self.indices[index]%len(eligible)]
                    self.indices[index]+=1
                # Finish the entire playlist before advancing to the next.
                if p["order"]=="shuffle":
                    if not self.shuffled[index]: self.position+=1
                elif self.indices[index]%len(eligible)==0:
                    self.position+=1
                return effect
            self.position+=1
        return None
