# KDE ASCII Saver V47: Gallery memory hotfix and settings usability

This release responds to a real-world KDE Plasma 6.7.5 test of V46 on two monitors,
where viewing the GIF gallery caused Glycin loader memory consumption of 5–6.6 GiB.

## Main fix: no GIF decoder processes

- Pre-rendered the 37 bundled GIF effects offline into compact `.aspr` frame packs
  (ZIP containers holding compressed 224px RGBA frames, with up to 24 samples
  and durations). **Pillow is only needed when generating the packs; the
  installed application does not depend on Pillow.** The packs are included.
- GTK4 uses `Gdk.MemoryTexture` constructed directly from the small RGBA frames.
  No GTK/GdkPixbuf/Glycin GIF loader is used to present effect thumbnails.
- Both the Effect Library and Visual Playlist Editor activate thumbnails
  only while their cards intersect the scrolled window's actual viewport,
  plus a small scrolling margin. Offscreen readers stop timers and close files.
- Closing the gallery explicitly cancels every playback timer, closes every
  pack and clears its last texture. Opening the gallery lazily recreates them.
- Target preview cadence is about 8 FPS, independent of screensaver output FPS,
  to avoid a continuous high-frequency GTK texture allocation workload.

## Preferences

- Unsaved-state banner now compares a full current form snapshot with its last
  saved snapshot. Reverting switches, sliders, checkboxes, colors, text, and
  font to their original values hides the banner and disables Save again.
- Background uses the same native GTK color picker as the shared palette.
- Each advanced slider shows its current value and labeled min/max marks.

## Tests and limitations

- Archive and decoder-free asset checks verify 37 bounded, independently
  decodable frame packs with different first and middle frames.
- Python tests and shell syntax are verified offline.
- Full GTK/Wayland runtime isn't present in the build environment and needs
  testing on CachyOS. In particular, allocation and scroll clipping behavior
  should be validated on your desktop. Renderer and KWin are unchanged.
- Changes only apply after quitting V46 and starting V47; residual processes
  from the old Glycin-based gallery may need their originating V46 app closed.
