"""Pure, bounded RGB(A) raster -> monochrome character-cell artwork.

No GTK, Pillow, filesystem operations or process execution. Pixel data is
provided by the image decoder (GdkPixbuf in the UI). The conversion renders
into a grid of terminal cells, not square bitmap pixels.
"""
from __future__ import annotations

from dataclasses import dataclass

# Dark to light; preserve a final space for white paper/background.
RAMPS = {
    'Classic': '@%#*+=-:. ',
    'Fine detail': '$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,"^`\'. ',
    'Minimal': '#*:. ',
}
# The custom option is not a built-in ramp; saved recipes carry its own
# validated, printable ASCII density characters. The lightest cell is always
# a blank space, appended automatically for predictable white backgrounds.
CUSTOM_RAMP_NAME = 'Custom'
AVAILABLE_RAMPS = (*RAMPS, CUSTOM_RAMP_NAME)
DEFAULT_CUSTOM_RAMP = '@#*:.'


def validate_custom_ramp(ramp: str) -> None:
    if (not isinstance(ramp, str) or not 2 <= len(ramp) <= 63
            or len(set(ramp)) != len(ramp)
            or any(not 33 <= ord(ch) <= 126 for ch in ramp)):
        raise ValueError('Custom ramp needs 2–63 different printable ASCII symbols, darkest first, without spaces. A lightest blank is added automatically.')


@dataclass(frozen=True)
class PhotoSettings:
    columns: int = 70
    rows: int = 28
    fit: str = 'crop'  # 'crop' or 'fit' (with whitespace padding)
    brightness: int = 0  # percentage points, -100..100
    contrast: int = 100  # percentage: 0..200
    invert: bool = False
    ramp: str = 'Classic'
    cell_aspect: float = 0.52  # monospace glyph physical width / line height
    gamma: float = 1.0  # 0.5..2.5, >1 brightens midtones
    edge: int = 0  # 0..100, local unsharp masking after sampling
    dither: bool = False  # Floyd-Steinberg luminance error diffusion
    posterize: int = 0  # 0 = off; otherwise 2..8 luminance bands
    alpha_background: str = 'white'  # white, gray or black behind RGBA pixels
    custom_ramp: str = DEFAULT_CUSTOM_RAMP  # dark -> light symbols, excluding final implicit blank

    def validate(self) -> None:
        if not 16 <= self.columns <= 120 or not 8 <= self.rows <= 60:
            raise ValueError('ASCII size must be 16–120 columns and 8–60 rows.')
        if self.fit not in ('crop', 'fit'):
            raise ValueError('Fit must be crop or fit.')
        if not -100 <= self.brightness <= 100 or not 0 <= self.contrast <= 200:
            raise ValueError('Brightness or contrast is outside its supported range.')
        if self.ramp not in AVAILABLE_RAMPS:
            raise ValueError('Unknown character ramp.')
        validate_custom_ramp(self.custom_ramp)
        if not 0.3 <= self.cell_aspect <= 1:
            raise ValueError('Invalid character aspect ratio.')
        if not 0.5 <= self.gamma <= 2.5:
            raise ValueError('Gamma must be between 0.5 and 2.5.')
        if not 0 <= self.edge <= 100:
            raise ValueError('Edge definition must be between 0 and 100.')
        if not isinstance(self.dither, bool):
            raise ValueError('Dithering must be on or off.')
        if type(self.posterize) is not int or self.posterize not in (0, 2, 3, 4, 5, 6, 7, 8):
            raise ValueError('Posterization must be off or 2–8 tones.')
        if self.alpha_background not in ('white', 'gray', 'black'):
            raise ValueError('Transparency background must be white, gray or black.')


def photo_to_ascii(pixels: bytes, width: int, height: int, *,
                   channels: int = 3, rowstride: int | None = None,
                   settings: PhotoSettings | None = None) -> str:
    """Convert packed RGB/RGBA data, respecting row padding and transparency.

    Fit pads with spaces; crop uses a centered source rectangle. Alpha is
    composited against the selected neutral background (white by default).
    Two-by-two sampling per cell smooths aliasing.
    Output contains exactly the requested number of rows/columns plus LF.
    """
    opts = settings or PhotoSettings()
    opts.validate()
    if not (0 < width <= 4096 and 0 < height <= 4096):
        raise ValueError('Invalid image dimensions.')
    if channels not in (3, 4):
        raise ValueError('Only RGB and RGBA image data are supported.')
    stride = rowstride if rowstride is not None else width * channels
    if stride < width * channels or stride > 4096 * 4 + 64:
        raise ValueError('Invalid image rowstride.')
    if len(pixels) < (height - 1) * stride + width * channels:
        raise ValueError('Incomplete image pixel buffer.')

    target_aspect = (opts.columns * opts.cell_aspect) / opts.rows
    source_aspect = width / height

    def source_position(u: float, v: float):
        if opts.fit == 'fit':
            if source_aspect > target_aspect:
                fraction = target_aspect / source_aspect
                if not (0 <= (v - (1 - fraction) / 2) < fraction):
                    return None
                v = (v - (1 - fraction) / 2) / fraction
            else:
                fraction = source_aspect / target_aspect
                if not (0 <= (u - (1 - fraction) / 2) < fraction):
                    return None
                u = (u - (1 - fraction) / 2) / fraction
        elif source_aspect > target_aspect:
            fraction = target_aspect / source_aspect
            u = (1 - fraction) / 2 + u * fraction
        else:
            fraction = source_aspect / target_aspect
            v = (1 - fraction) / 2 + v * fraction
        return min(width - 1, max(0, int(u * width))), min(height - 1, max(0, int(v * height)))

    # Sampling, tone correction and glyph quantization are separate stages.
    # Missing samples in the fit/letterbox area stay literal spaces and never
    # participate in sharpening or dithering. This also prevents dark halos
    # around padded artwork.
    matte = {'white': 255, 'gray': 128, 'black': 0}[opts.alpha_background]
    values: list[list[float | None]] = []
    for row in range(opts.rows):
        samples: list[float | None] = []
        for col in range(opts.columns):
            gray_sum = 0.0
            count = 0
            for dy in (-0.2, 0.2):
                for dx in (-0.2, 0.2):
                    position = source_position((col + 0.5 + dx) / opts.columns,
                                               (row + 0.5 + dy) / opts.rows)
                    if position is None:
                        continue
                    x, y = position
                    i = y * stride + x * channels
                    r, g, b = pixels[i], pixels[i + 1], pixels[i + 2]
                    gray = (2126 * r + 7152 * g + 722 * b) / 10000
                    if channels == 4:
                        alpha = pixels[i + 3] / 255
                        gray = gray * alpha + matte * (1 - alpha)
                    gray_sum += gray
                    count += 1
            if not count:
                samples.append(None)
                continue
            gray = gray_sum / count
            if opts.gamma != 1.0:
                gray = 255 * (gray / 255) ** (1 / opts.gamma)
            gray = (gray - 127.5) * opts.contrast / 100 + 127.5
            gray += opts.brightness * 255 / 100
            gray = min(255, max(0, gray))
            if opts.invert:
                gray = 255 - gray
            if opts.posterize:
                bands = opts.posterize - 1
                gray = 255 * int(gray * bands / 255 + 0.5) / bands
            samples.append(gray)
        values.append(samples)

    if opts.edge:
        # Use the original sampled grid for every neighbor lookup, so one
        # adjusted pixel never feeds back into another edge calculation.
        strength = opts.edge / 100 * 1.5
        sharpened: list[list[float | None]] = []
        for row, samples in enumerate(values):
            line: list[float | None] = []
            for col, center in enumerate(samples):
                if center is None:
                    line.append(None)
                    continue
                neighbors = [values[y][x]
                             for y, x in ((row - 1, col), (row + 1, col),
                                          (row, col - 1), (row, col + 1))
                             if 0 <= y < opts.rows and 0 <= x < opts.columns
                             and values[y][x] is not None]
                if not neighbors:
                    line.append(center)
                    continue
                local_mean = sum(neighbors) / len(neighbors)
                line.append(min(255, max(0, center + strength * (center - local_mean))))
            sharpened.append(line)
        values = sharpened

    symbols = (opts.custom_ramp + ' ' if opts.ramp == CUSTOM_RAMP_NAME
               else RAMPS[opts.ramp])
    # Error diffusion is spatial: a medium tone can use a mixture of glyphs
    # instead of the same glyph everywhere. It remains optional and is off by
    # default to preserve V87 output and the cleaner non-dithered typography.
    errors = [[0.0] * opts.columns for _ in range(opts.rows)] if opts.dither else None
    output: list[str] = []
    for row, samples in enumerate(values):
        line = []
        for col, original in enumerate(samples):
            if original is None:
                line.append(' ')
                continue
            gray = original
            if errors is not None:
                gray = min(255, max(0, gray + errors[row][col]))
            index = min(len(symbols) - 1, int(gray / 255 * (len(symbols) - 1) + 0.5))
            line.append(symbols[index])
            if errors is not None:
                residual = gray - index * 255 / (len(symbols) - 1)
                for y, x, weight in ((row, col + 1, 7 / 16),
                                     (row + 1, col - 1, 3 / 16),
                                     (row + 1, col, 5 / 16),
                                     (row + 1, col + 1, 1 / 16)):
                    if (0 <= y < opts.rows and 0 <= x < opts.columns
                            and values[y][x] is not None):
                        errors[y][x] += residual * weight
        output.append(''.join(line))
    return '\n'.join(output) + '\n'
