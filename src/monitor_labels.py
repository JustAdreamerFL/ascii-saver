"""Display-count-aware UI labels, independent of GTK for regression testing."""


def playback_title(count: int) -> str:
    """Label for the currently connected output count."""
    if count == 1:
        return "Start on this display"
    if count > 1:
        return "Start on all displays"
    return "Start screensaver"


def connected_displays(count: int) -> str:
    if count == 1:
        return "1 display connected"
    return f"{max(0, count)} displays connected"
