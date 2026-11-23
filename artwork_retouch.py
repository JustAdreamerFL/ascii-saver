"""Pure, bounded tools for manual retouch of monospaced ASCII artwork.

No file I/O and no GTK dependency: previews and undo history stay in the editor.
Offsets are character offsets, matching Gtk.TextIter.get_offset().
"""
from __future__ import annotations

# Reversing a line also changes the facing direction of asymmetric symbols.
MIRROR = str.maketrans('()[]{}<>/\\', ')(][}{><\\/')
MAX_SELECTION = 200_000


def validate_ink(glyph: str) -> str:
    if not isinstance(glyph, str) or len(glyph) != 1 or not 32 <= ord(glyph) <= 126:
        raise ValueError('Choose one printable ASCII character (space through ~).')
    return glyph


def paint_at(text: str, offset: int, glyph: str, *, erase: bool = False) -> tuple[str, int]:
    """Replace one cell under the caret, or append before a newline.

    Erase replaces an existing cell with a space, never extends the canvas.
    The next caret position is provided for the GTK text buffer controller.
    """
    if not isinstance(text, str) or not isinstance(offset, int) or not 0 <= offset <= len(text):
        raise ValueError('Caret is outside the artwork.')
    ink = ' ' if erase else validate_ink(glyph)
    if erase and (offset == len(text) or text[offset] in '\r\n'):
        return text, offset
    if offset < len(text) and text[offset] not in '\r\n':
        return text[:offset] + ink + text[offset + 1:], offset + 1
    return text[:offset] + ink + text[offset:], offset + 1


def _selected_lines(text: str) -> tuple[list[str], bool]:
    if not isinstance(text, str):
        raise ValueError('Invalid text selection.')
    if len(text) > MAX_SELECTION:
        raise ValueError('Selection is too large to retouch at once.')
    if '\r' in text or '\x00' in text:
        raise ValueError('Select ordinary text lines only.')
    trailing = text.endswith('\n')
    body = text[:-1] if trailing else text
    return body.split('\n'), trailing


def mirror_selection(text: str) -> str:
    """Mirror a selected region horizontally, retaining rectangular alignment."""
    lines, trailing = _selected_lines(text)
    width = max(map(len, lines), default=0)
    result = '\n'.join(line.ljust(width)[::-1].translate(MIRROR) for line in lines)
    return result + ('\n' if trailing else '')


def flip_selection(text: str) -> str:
    """Flip selected rows vertically, preserving the final newline if any."""
    lines, trailing = _selected_lines(text)
    result = '\n'.join(reversed(lines))
    return result + ('\n' if trailing else '')


def paint_selection(text: str, glyph: str, *, erase: bool = False) -> str:
    """Fill selected cells but preserve line breaks and selected geometry."""
    if len(text) > MAX_SELECTION:
        raise ValueError('Selection is too large to paint.')
    replacement = ' ' if erase else validate_ink(glyph)
    return ''.join(char if char in '\r\n' else replacement for char in text)
