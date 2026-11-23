"""Work out whether an ASCII logo fits a terminal's character grid.

Terminal width is in cells, not Unicode codepoints; use the same width rules
as the final-frame formatter, while keeping measurements independent from GTK.
"""
from final_frame import _cell_width, _clean_line


def artwork_cells(text: str) -> tuple[int, int]:
    lines = text.splitlines()
    if not lines:
        return (0, 0)
    return (max(sum(_cell_width(c) for c in _clean_line(line)) for line in lines), len(lines))


def fit_ratio(art_columns: int, art_rows: int, columns: int, rows: int) -> float:
    """Font scale necessary to fit the supplied dimensions (1 if fits)."""
    if columns <= 0 or rows <= 0:
        return 1.0  # Layout not measured yet; never guess.
    ratio_w = columns / art_columns if art_columns > 0 else 1.0
    ratio_h = rows / art_rows if art_rows > 0 else 1.0
    return min(1.0, ratio_w, ratio_h)


def suggested_point_size(size_pt: float, logo_cells: tuple[int, int],
                         terminal_cells: tuple[int, int], minimum_pt: float = 7.0) -> float:
    """Round down to a safe point size, leaving a little room for VTE padding."""
    import math
    ratio = fit_ratio(*logo_cells, *terminal_cells)
    if ratio >= 1:
        return size_pt
    return max(minimum_pt, math.floor((size_pt * ratio * 0.96) * 2) / 2)


def choose_artwork_font_sizes(
    size_pt: float,
    artwork_by_monitor: dict[str, tuple[int, int]],
    monitor_cells: dict[str, tuple[int, int]], *,
    auto_fit: bool,
    independent: bool,
) -> dict[str, float]:
    """Calculate a fresh font plan from the *configured* font for every display.

    Independent mode fits each display's actual artwork to its own geometry.
    Shared mode uses the smallest proposed font across all active displays,
    preventing inconsistent sizing on landscape/portrait combinations.
    Missing or empty artwork does not force an unnecessary shrink.
    Turning auto-fit off always returns the original font size.
    """
    if not auto_fit:
        return {name: size_pt for name in monitor_cells}
    proposals = {
        name: suggested_point_size(
            size_pt, artwork_by_monitor.get(name, (0, 0)), viewport
        )
        for name, viewport in monitor_cells.items()
    }
    if independent or not proposals:
        return proposals
    common = min(proposals.values())
    return {name: common for name in proposals}


def choose_font_sizes(size_pt: float, logo_cells: tuple[int, int],
                      monitor_cells: dict[str, tuple[int, int]], *,
                      auto_fit: bool, independent: bool) -> dict[str, float]:
    """Compatibility wrapper for the same artwork on all displays."""
    return choose_artwork_font_sizes(
        size_pt,
        {name: logo_cells for name in monitor_cells},
        monitor_cells,
        auto_fit=auto_fit,
        independent=independent,
    )
