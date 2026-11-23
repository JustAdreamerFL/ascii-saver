"""Palette-aware recoloring of compact, precomputed effect thumbnails.

At packaging time we turn the original colorful RGBA frames into one-byte
coverage masks. At runtime expansion to RGBA is a small native `bytes.join`
over a 256-entry color lookup table. We never need Pillow or a live renderer.
"""
from __future__ import annotations

# Original upstream GIF gallery frames have a common opaque #12121A backing.
# Do not sample the top-left pixel: some moving effects cover that position.
SOURCE_BACKGROUND = (18, 18, 26)
NOISE_FLOOR = 7


def coverage_mask(rgba: bytes) -> bytes:
    """Convert a packed RGBA sample to a one-byte-per-pixel coverage mask.

    Saturated colors of any hue are treated as artwork, not merely green/gray
    luma. Small antialias / resampling noise close to the original background
    is ignored. The sample alpha remains respected, if present.
    """
    if len(rgba) % 4:
        raise ValueError("RGBA frame size is not a multiple of four")
    result = bytearray(len(rgba) // 4)
    br, bg, bb = SOURCE_BACKGROUND
    for pixel in range(len(result)):
        off = pixel * 4
        strength = max(abs(rgba[off] - br),
                       abs(rgba[off + 1] - bg),
                       abs(rgba[off + 2] - bb)) - NOISE_FLOOR
        if strength > 0:
            value = min(255, (strength * 255 + 115) // 230)
            result[pixel] = value * rgba[off + 3] // 255
    return bytes(result)


def _rgb(hex_color: str) -> tuple[int, int, int]:
    if not isinstance(hex_color, str) or len(hex_color) != 7 or hex_color[0] != '#':
        raise ValueError(f'Invalid preview RGB color: {hex_color!r}')
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    except ValueError as error:
        raise ValueError(f'Invalid preview RGB color: {hex_color!r}') from error


def tint_mask(mask: bytes, foreground: str, background: str) -> bytes:
    """Expand a grayscale coverage mask to opaque RGBA in selected colors.

    The 256 tiny RGBA entries are built once per frame. Bytes are combined by
    C-level join rather than doing arithmetic per pixel in the GTK event loop.
    """
    fr, fg, fb = _rgb(foreground)
    br, bg, bb = _rgb(background)
    table = tuple(bytes((br + ((fr - br) * level + 127) // 255,
                         bg + ((fg - bg) * level + 127) // 255,
                         bb + ((fb - bb) * level + 127) // 255,
                         255)) for level in range(256))
    return b''.join(table[level] for level in mask)
