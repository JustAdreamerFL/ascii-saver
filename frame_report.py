"""Parse ttfx per-effect frame reports without trusting malformed output."""
import math


def parse_frame_report(report, expected_effect=None):
    if not isinstance(report, dict) or report.get("schema") not in (1, 2):
        return None
    if report.get("status") != "completed":
        return None
    effect = report.get("effect")
    if not isinstance(effect, str) or not effect or (expected_effect and effect != expected_effect):
        return None
    frames = report.get("frames_written")
    if type(frames) is not int or frames < 0:
        return None
    def valid_float(key):
        value = report.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(key)
        return float(value)
    try:
        elapsed = valid_float("elapsed_seconds")
        average = valid_float("average_output_fps")
        active = report.get("active_output_fps")
        if report["schema"] == 2 and active is not None:
            active = valid_float("active_output_fps")
        else:
            active = None
    except ValueError:
        return None
    return {"output_frames": frames, "output_fps": average,
            "active_output_fps": active, "output_seconds": elapsed,
            "frame_stats_schema": report["schema"]}
