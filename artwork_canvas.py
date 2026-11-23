"""Bounded ASCII grid and stroke operations for the artwork editor.

No GTK and no file I/O. Canvas is an alternate view of the same text buffer.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import unicodedata
from artwork_retouch import validate_ink

MAX_COLS = 200
MAX_ROWS = 100
MAX_TEXT = 200_000
MIN_COLS = 48
MIN_ROWS = 18


@dataclass(frozen=True)
class CanvasShape:
    cols: int
    rows: int


def _lines(text: str) -> tuple[list[str], bool]:
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        raise ValueError('Artwork is too large for the mouse canvas; use Text mode.')
    # Most terminal artwork uses box-drawing characters (including the bundled
    # sample logo). These are ordinary *one-cell* glyphs and must not force the
    # editor into Text mode. Reject only characters with ambiguous grid geometry:
    # control/format and combining codepoints, and two-cell CJK/emoji glyphs.
    def one_cell(char):
        return (char.isprintable()
                and not unicodedata.category(char).startswith('M')
                and unicodedata.east_asian_width(char) not in ('W', 'F'))
    if any(char != '\n' and not one_cell(char) for char in text):
        raise ValueError('Draw mode needs single-column glyphs; use Text mode for tabs, combining marks or wide glyphs.')
    trailing = text.endswith('\n')
    lines = (text[:-1] if trailing else text).split('\n')
    if len(lines) > MAX_ROWS or any(len(line) > MAX_COLS for line in lines):
        raise ValueError('Artwork exceeds the 200-column / 100-row mouse canvas limit.')
    return lines, trailing


def validate_workspace(workspace: CanvasShape) -> CanvasShape:
    """Validate a view-only drawing extent; never truncate existing artwork."""
    if (not isinstance(workspace, CanvasShape)
            or isinstance(workspace.cols, bool) or isinstance(workspace.rows, bool)
            or not isinstance(workspace.cols, int) or not isinstance(workspace.rows, int)
            or not MIN_COLS <= workspace.cols <= MAX_COLS
            or not MIN_ROWS <= workspace.rows <= MAX_ROWS):
        raise ValueError('Work area must be 48–200 columns by 18–100 rows.')
    return workspace


def canvas_shape(text: str, workspace: CanvasShape | None = None) -> CanvasShape:
    """Visible work area includes all artwork plus optional *unpainted* cells."""
    lines, _ = _lines(text)
    requested = validate_workspace(workspace) if workspace is not None else CanvasShape(MIN_COLS, MIN_ROWS)
    return CanvasShape(max(requested.cols, max(map(len, lines), default=0)),
                       max(requested.rows, len(lines)))


def line_cells(x0: int, y0: int, x1: int, y1: int) -> tuple[tuple[int, int], ...]:
    """Inclusive Bresenham raster, so quick mouse movement has no gaps."""
    if any(not isinstance(v, int) or abs(v) > MAX_TEXT for v in (x0, y0, x1, y1)):
        raise ValueError('Stroke coordinate outside supported limits.')
    result = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        result.append((x0, y0))
        if (x0, y0) == (x1, y1):
            break
        twice = 2 * error
        if twice >= dy:
            error += dy
            x0 += sx
        if twice <= dx:
            error += dx
            y0 += sy
    return tuple(result)


def paint_stroke(text: str, cells, ink: str, *, erase: bool = False,
                 workspace: CanvasShape | None = None) -> str:
    """Paint unique grid cells, extending short rows only when painting.

    Erase never expands a line or adds rows. Existing line endings and all
    untouched whitespace survive byte-for-byte.
    """
    lines, trailing = _lines(text)
    glyph = ' ' if erase else validate_ink(ink)
    shape = canvas_shape(text, workspace)
    unique = set()
    for coordinate in cells:
        if not isinstance(coordinate, tuple) or len(coordinate) != 2:
            raise ValueError('Invalid canvas coordinate.')
        x, y = coordinate
        if not isinstance(x, int) or not isinstance(y, int) or not (0 <= x < shape.cols and 0 <= y < shape.rows):
            raise ValueError('Stroke outside the canvas.')
        unique.add((x, y))
    for x, y in sorted(unique, key=lambda c: (c[1], c[0])):
        if erase and (y >= len(lines) or x >= len(lines[y])):
            continue
        while y >= len(lines):
            lines.append('')
        line = lines[y]
        if x >= len(line):
            line = line.ljust(x + 1)
        if line[x] != glyph:
            lines[y] = line[:x] + glyph + line[x + 1:]
    result = '\n'.join(lines) + ('\n' if trailing else '')
    if len(result) > MAX_TEXT:
        raise ValueError('Resulting artwork exceeds the canvas safety limit.')
    return result


ZOOM_LEVELS = (75, 100, 125, 150, 200)


def canvas_cell_at(x: float, y: float, shape: CanvasShape,
                   cell_width: int, cell_height: int, *, padding: int = 16):
    """Map GTK drawing-area logical coordinates to an ASCII character cell.

    GTK input events and Pango pixel extents are both expressed in logical
    widget units. Never apply the monitor's scale factor a second time.
    """
    if not all(math.isfinite(v) for v in (x, y)):
        return None
    if cell_width <= 0 or cell_height <= 0:
        raise ValueError('Character-cell dimensions must be positive.')
    col = math.floor((x - padding) / cell_width)
    row = math.floor((y - padding) / cell_height)
    if 0 <= col < shape.cols and 0 <= row < shape.rows:
        return col, row
    return None


def zoom_scroll_offset(old_scroll: float, old_cell: int, new_cell: int,
                       *, padding: int = 16) -> float:
    """Preserve the logical top-left visible character on changing zoom.

    The caller clamps the returned position after GTK has allocated the new
    scrollable content size. Zero scroll remains zero, avoiding a startup jump.
    """
    if not math.isfinite(old_scroll) or old_scroll < 0:
        raise ValueError('Invalid scroll position.')
    if old_cell <= 0 or new_cell <= 0:
        raise ValueError('Character-cell dimensions must be positive.')
    if old_scroll <= padding:
        return old_scroll
    return padding + (old_scroll - padding) * new_cell / old_cell


KEYBOARD_DIRECTIONS = {
    'left': (-1, 0), 'right': (1, 0),
    'up': (0, -1), 'down': (0, 1),
}


def move_canvas_cursor(cell: tuple[int, int], direction: str,
                       shape: CanvasShape) -> tuple[int, int]:
    """Move an accessible drawing cursor, clamped to the existing canvas grid."""
    if direction not in KEYBOARD_DIRECTIONS:
        raise ValueError('Unsupported drawing direction.')
    col, row = cell
    if (not isinstance(col, int) or isinstance(col, bool)
            or not isinstance(row, int) or isinstance(row, bool)
            or not 0 <= col < shape.cols or not 0 <= row < shape.rows):
        raise ValueError('Invalid drawing cursor.')
    dx, dy = KEYBOARD_DIRECTIONS[direction]
    return max(0, min(shape.cols - 1, col + dx)), max(0, min(shape.rows - 1, row + dy))


def canvas_reveal_offset(scroll: float, page_size: float,
                         cell_start: float, cell_extent: float) -> float:
    """Keep the keyboard cursor visible in a scrollable GTK viewport.

    Returns the desired unconstrained position; GTK callers clamp to the
    adjustment's actual limits. No scrolling occurs if the cell is visible.
    """
    if not all(math.isfinite(v) for v in (scroll, page_size, cell_start, cell_extent)):
        raise ValueError('Invalid viewport dimensions.')
    if scroll < 0 or page_size <= 0 or cell_start < 0 or cell_extent <= 0:
        raise ValueError('Invalid viewport dimensions.')
    margin = min(8.0, page_size / 4.0)
    if cell_start < scroll + margin:
        return max(0.0, cell_start - margin)
    if cell_start + cell_extent > scroll + page_size - margin:
        return max(0.0, cell_start + cell_extent - page_size + margin)
    return scroll


def visible_cell_range(scroll: float, page_size: float, cell_size: int, count: int,
                       *, padding: int = 16) -> tuple[int, int]:
    """Return the [start, stop) cells near a scroll viewport, plus one guard cell.

    Drawing only these columns/rows avoids re-layout of off-screen 200 x 100 art.
    A zero page size (unrealized widget) conservatively selects all cells.
    """
    if (not math.isfinite(scroll) or not math.isfinite(page_size)
            or scroll < 0 or page_size < 0 or cell_size <= 0 or count < 0):
        raise ValueError('Invalid scroll viewport.')
    if page_size == 0:
        return 0, count
    start = min(count, max(0, math.floor((scroll - padding) / cell_size) - 1))
    end = min(count, max(start, math.ceil((scroll + page_size - padding) / cell_size) + 1))
    return start, end
