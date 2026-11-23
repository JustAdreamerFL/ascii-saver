# ASCII Saver V93 (0.93.0): Photo finishing tools

**Date:** 2026-11-08. Experimental source build, not a validated desktop release.

## Implemented

- **Posterization:** Select Off or 2–8 luminance bands in the collapsed
  Advanced section. Applied after the usual brightness, contrast, gamma and
  inversion adjustments, before optional edge enhancement, dithering and
  character mapping. This produces real graphic/retro density differences,
  not merely a new label. Default is Off, matching earlier releases.
- **Transparency matte:** Transparent regions in RGBA photos can be composited
  on white, mid-gray or black. Default remains white, so legacy results are
  preserved. The matte chooser is insensitive for RGB sources without an
  alpha channel. A cropped/fit letterbox region stays literal whitespace,
  independent of the selected backdrop.
- **Live and safe workflow:** New controls participate in the 80 ms coalesced
  preview update, reset, built-in creative looks, personal presets, project
  reopen, Save as New Artwork and explicit Use in Editor. There is no change
  to the original photo, existing artwork, renderer or online assets.
- **Creative examples:** Graphic Ink now uses three graphic tone bands;
  8-Bit Arcade uses four. All other built-in looks retain their original
  base behavior, with neutral posterization and white transparency matte.

## Compatibility

Previously saved V89–V92 project manifests and V91–V92 personal presets
contain the earlier `PhotoSettings` keys. The validated settings decoder
permits exactly the two new fields to be absent and fills their neutral
values. Existing format-version-1 JSON files remain valid; newly saved
files include both fields. Unexpected keys, missing pre-V93 keys and invalid
value types are still rejected rather than guessed.

## Verification

Headless regressions cover neutral-default parity, quantization bands, alpha
compositing, opaque RGB/RGBA parity, fitted whitespace padding, incorrect
settings, saved new recipes, legacy project/preset loading and UI wiring.
The installation, desktop detection and all prior effect previews are checked
separately. Native GTK visual, keyboard and Wayland tests remain unverified.

## Remaining work

Evaluate additional advanced blur or alternative sharpening only with a
meaningful visual reason. Full live GNOME/KDE acceptance, and the V92 online
source's actual HTTPS availability and rights, remain open.
