# ASCII Saver V94 (0.94.0): Creative character ramps

**Date:** 2026-11-08. Experimental source build, not a validated desktop release.

## New user-facing workflow

Within **Artwork Editor → Photo to ASCII**, choose **Custom** from the normal
ASCII style list. The Advanced image tools section expands and enables the
custom characters field. Enter your preferred sequence from darkest to
lightest, for example `@#*:.`. The final, lightest tone is always a space and
need not be typed. You may use punctuation, letters and digits; each symbol
must occur once. Valid sequences contain **2–63 distinct printable ASCII
characters (U+0021–U+007E)**, with no embedded spaces, controls or Unicode
width ambiguity. The default three ramps remain unchanged.

The image and ASCII preview still display side by side, or stack in a narrow
window, with the existing 80 ms coalesced refresh. Invalid input clears the
old ASCII preview and disables both Use in Editor and Save as New Artwork; a
readable status explains the problem. Editing an incomplete ramp does not
produce an error toast on every keystroke. Returning to a standard style
works even while a custom input is incomplete.

## Persistence and compatibility

Custom ramps are part of the typed PhotoSettings recipe. They are saved with
new photo project manifests and named personal conversion presets, then
restored on reopen. Recipes from V89–V93 that lack the new field load using a
safe default, preserving earlier output when a standard ramp is selected.
The renderer receives only the usual plain `.txt` with printable ASCII, and
no color escape sequences are introduced. The original photo and prior
artwork files remain unchanged until explicit export.

## Tests and limitations

Headless tests verify endpoint and mid-tone mappings, preservation of the
standard ramps, malformed/duplicate/Unicode/control-character rejection,
exact project/preset round trips, legacy recipe migration, and static GTK
wiring for live updates and safe export. Previous unit, installer and
session-detection checks run as a cumulative regression suite.

**Not yet validated:** actual GTK/libadwaita view, VTE glyph width and colors,
keyboard navigation, KWin/GNOME taskbar/window behavior, and live remote
ascii-bin HTTPS access. ANSI output is deliberately not enabled.
