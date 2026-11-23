"""Safe ANSI-free final artwork frame with original ASCII layout preserved."""
from __future__ import annotations
import unicodedata


def _cell_width(char: str) -> int:
    if unicodedata.combining(char) or unicodedata.category(char) in ('Mn', 'Me', 'Cf'):
        return 0
    return 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1


def _expand_tabs(line: str, tabstop: int = 8) -> str:
    out = []
    column = 0
    for char in line:
        if char == '\t':
            padding = tabstop - column % tabstop
            out.append(' ' * padding)
            column += padding
        else:
            out.append(char)
            column += _cell_width(char)
    return ''.join(out)


def _clean_line(line: str) -> str:
    # Never feed control sequences from edited user artwork into VTE.
    return _expand_tabs(''.join(c for c in line if c == '\t' or (c.isprintable() and c != '\x1b')))


def _clip_cells(line: str, max_cells: int) -> tuple[str, int]:
    output = []
    used = 0
    for char in line:
        width = _cell_width(char)
        if used + width > max_cells:
            break
        if width == 0 and not output:
            continue
        output.append(char)
        used += width
    return ''.join(output), used


def centered_frame(text: str, columns: int, rows: int) -> bytes:
    """Draw the artwork as one centered rectangle, retaining indentation."""
    if columns < 1 or rows < 1:
        return b''
    lines = [_clean_line(line) for line in text.replace('\r\n', '\n').replace('\r', '\n').splitlines()]
    if not lines:
        return b'\x1b[2J\x1b[H'
    width = max(sum(_cell_width(c) for c in line) for line in lines)
    start_column = max(0, (columns - min(width, columns)) // 2)
    start_row = max(0, (rows - min(len(lines), rows)) // 2)
    parts = ['\x1b[2J\x1b[H']
    for row, line in enumerate(lines[:rows]):
        visible, _ = _clip_cells(line, columns)
        parts.append(f'\x1b[{start_row + row + 1};{start_column + 1}H{visible}')
    return ''.join(parts).encode('utf-8')
