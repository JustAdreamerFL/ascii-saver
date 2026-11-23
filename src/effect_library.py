"""Pure filtering for the graphical effect library."""
from playlist_engine import group

def select_effects(names, search="", duration="all", intensity="all"):
    """Preserve library order; filter by substring and qualitative metadata."""
    query = search.strip().casefold()
    valid_durations = {"all", "short", "medium", "long"}
    valid_intensities = {"all", "gentle", "moderate", "energetic"}
    if duration not in valid_durations or intensity not in valid_intensities:
        raise ValueError("unknown filter")
    return [name for name in names if query in name.casefold()
            and (duration == "all" or group(name)["duration"] == duration)
            and (intensity == "all" or group(name)["intensity"] == intensity)]
