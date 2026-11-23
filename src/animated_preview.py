"""Viewport-controlled, low-memory GTK4 effect previews.

Tinted thumbnails use precomputed downscaled grayscale masks: neither GTK's
Glycin GIF loader nor GdkPixbufAnimation loads the upstream 588x169 GIFs.
The compressed pack is held only while its card is inside the viewport.
"""
from __future__ import annotations

from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gdk, GLib, Gtk
from preview_asset import PackedPreview
from preview_tint import tint_mask


class AnimatedPreview(Gtk.Picture):
    def __init__(self, path: Path, width: int = 230, height: int = 105,
                 foreground: str = '#F2F2F2', background: str = '#000000'):
        super().__init__()
        self._path = Path(path)
        self._foreground = foreground
        self._background = background
        self.set_can_shrink(True)
        self.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.set_size_request(width, height)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.CENTER)
        self._pack = None
        self._frame = 0
        self._timer = None
        self._active = False
        self.connect('unmap', self._unmapped)
        # A single 224px tinted RGBA frame uses only ~56 KiB. Draw its poster even
        # before the card is scrolled into view, so the library is never blank.
        # Crucially, do NOT decode or retain the rest of the animation.
        self.show_poster()

    def show_poster(self) -> None:
        """Show just frame zero, without retaining the compressed pack."""
        if self._active or self.get_paintable() is not None:
            return
        try:
            with PackedPreview(self._path) as pack:
                self._set_frame_texture(pack, 0)
        except (OSError, ValueError, KeyError, RuntimeError) as error:
            self.set_tooltip_text(f'Preview unavailable: {error}')

    def set_colors(self, foreground: str, background: str) -> None:
        """Apply live palette edits without restarting an animation timer.

        Only the currently playing/visible cards are re-tinted immediately.
        Unused posters are invalidated, not decoded in a hidden window.
        """
        if (foreground, background) == (self._foreground, self._background):
            return
        self._foreground, self._background = foreground, background
        if self._active and self._pack is not None:
            self._paint(self._frame)
        else:
            # Off-viewport cards may still count as GTK-mapped. Avoid decoding
            # all 37 posters for each intermediate color-picker update. A
            # newly exposed card redraws when set_playing(True) starts it.
            self.set_paintable(None)

    def _set_frame_texture(self, pack: PackedPreview, index: int) -> None:
        pixels = GLib.Bytes.new(tint_mask(
            pack.mask_frame(index), self._foreground, self._background))
        self.set_paintable(Gdk.MemoryTexture.new(
            pack.width, pack.height, Gdk.MemoryFormat.R8G8B8A8,
            pixels, pack.width * 4))

    def set_playing(self, playing: bool) -> None:
        if playing and self.get_mapped():
            if not self._active:
                self._start()
        else:
            self.pause()

    def _start(self):
        if self._active:
            return
        try:
            self._pack = PackedPreview(self._path)
            self._frame = 0
            self._active = True
            self._paint(self._frame)
            if self._pack.frame_count > 1:
                self._schedule()
        except Exception as error:
            self.pause()
            self.set_tooltip_text(f'Preview unavailable: {error}')

    def _paint(self, index: int):
        pack = self._pack
        if pack is None:
            return
        self._set_frame_texture(pack, index)

    def _schedule(self):
        pack = self._pack
        if self._active and pack is not None and self.get_mapped():
            self._timer = GLib.timeout_add(pack.delays[self._frame], self._tick)

    def _tick(self):
        self._timer = None
        if self._active and self.get_mapped() and self._pack is not None:
            self._frame = (self._frame + 1) % self._pack.frame_count
            self._paint(self._frame)
            self._schedule()
        return GLib.SOURCE_REMOVE

    def pause(self):
        self._active = False
        if self._timer is not None:
            GLib.source_remove(self._timer)
            self._timer = None
        if self._pack is not None:
            self._pack.close()
            self._pack = None

    def release(self):
        """Fully release textures, compressed data and timers when gallery closes."""
        self.pause()
        self.set_paintable(None)

    def _unmapped(self, *_args):
        self.pause()


def update_visible_previews(scroller: Gtk.ScrolledWindow, entries, margin: int = 70):
    """Activate only cards intersecting the clipped scroll viewport.

    GTK4 `mapped` alone is insufficient: offscreen children in a Gtk.Grid or
    Gtk.FlowBox are also mapped! Coordinates are relative to the scroller.
    """
    shown = scroller.get_mapped()
    height = scroller.get_height()
    width = scroller.get_width()
    for card, preview in entries:
        inside = False
        if shown and card.get_mapped() and card.get_visible():
            translated = card.translate_coordinates(scroller, 0.0, 0.0)
            if translated and translated[0]:
                _, x, y = translated
                inside = (y < height + margin and y + card.get_height() > -margin
                          and x < width + margin and x + card.get_width() > -margin)
        preview.set_playing(inside)
    return GLib.SOURCE_REMOVE
