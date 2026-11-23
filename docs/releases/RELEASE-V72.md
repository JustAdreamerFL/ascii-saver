# ASCII Saver V72 (0.72.0): palette-matched effect thumbnails

## What changed

- The **Effect Library** animated sample cards and their stationary posters now use the first selected global palette foreground color and the selected background, not their original hard-coded RGB gradients.
- Editing a global swatch or background while Preferences is open updates running library animations without restarting their timers. Discard restores the previous colors; Save persists them. Unseen cards are refreshed on demand.
- The **Playlist Editor** sample cards use the same global palette from saved configuration.
- All 37 `.aspr` animation archives contain a small one-byte-per-pixel color mask for every one of their 886 frames. Original sample artwork is retained in the archives for compatibility.
- Tinting requires no GIF decoder, no live renderer, and no new runtime dependencies. Only visible cards animate.

## How thumbnails choose a color

Previews represent sample artwork, not actual fullscreen rounds. They always show **the first global palette color**. If color cycling is enabled, live effects will move through colors **between effects**, as before. Per-display palette overrides continue to apply to fullscreen monitors but do not alter these shared library samples.

The mask preserves the outline and relative brightness of the colored source artwork but cannot reproduce the exact strength/shape of every native terminal glyph. This is a color-consistent sample rather than pixel-identical fullscreen rendering.

## Verification

- Pure-Python regression tests cover mask generation, saturation, alpha, tinting, precomputed asset completeness, legacy fallback, GTK-free integration contracts and installer inclusion.
- Per-frame tint throughput was measured on one representative 224 × 64 preview at roughly 0.8 ms using Python 3.13 in this environment. This is a local measurement, not an across-device benchmark.
- Full GTK4/VTE and Wayland runtime validation remains deferred until the user tests the cumulative release.
