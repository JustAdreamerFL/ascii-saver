"""Pure functions for accurate ttfx child-start lifecycle telemetry."""
from __future__ import annotations

def spawn_event(pending, success: bool, *, message: str = "", pid=None, timestamp: float):
    if pending is None:
        return None
    record = dict(pending)
    record.update(event="effect_start" if success else "effect_spawn_failed",
                  wall_timestamp=timestamp)
    if success:
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError("successful launch needs a positive PID")
        record["pid"] = pid
    else:
        record["error"] = str(message)
    return record
