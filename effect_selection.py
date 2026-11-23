"""Choose explicit effects so timing records can be attributed correctly."""
import random
from playlist_engine import EFFECTS


def select_effect(config, *, playlist_effect=None, shared_effect=None, rng=None, rotation=None):
    """Return a concrete ttfx effect, never a synthetic 'random' label."""
    excluded = set(config.get('exclude_effects', []))
    valid = [effect for effect in EFFECTS if effect not in excluded]
    if not valid:
        raise ValueError('All effects are excluded; enable at least one animation')
    for candidate in (playlist_effect, shared_effect):
        if candidate in valid:
            return candidate
    # Fullscreen independent monitors use their own shuffle bags rather than
    # random.choice(), so consecutive rounds do not repeat before exhausting
    # the enabled effects. Explicit playlists/shared effects take precedence.
    if rotation is not None:
        return rotation.next(valid)
    return (rng or random.SystemRandom()).choice(valid)


def effect_args(argv, name):
    """Append one validated concrete effect subcommand, preserving terminal flags.

    The application builds only terminal options here; filtering is performed
    by select_effect rather than forwarding --exclude-effects to ttfx.
    Legacy callers with a named effect or --random-effect remain supported.
    """
    if name not in EFFECTS:
        raise ValueError(f"Unknown ttfx effect: {name}")
    result = list(argv)
    if "--random-effect" in result:
        result.remove("--random-effect")
    if "--exclude-effects" in result:
        # Legacy argv contains a variable-length exclusion list. Only known
        # effect names belong to that list; the following flags must survive.
        pos = result.index("--exclude-effects")
        end = pos + 1
        while end < len(result) and result[end] in EFFECTS:
            end += 1
        del result[pos:end]
    if result and result[-1] in EFFECTS:
        result.pop()
    return result + [name]
