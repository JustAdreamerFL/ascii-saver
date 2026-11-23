# ASCII Saver V79 (0.79.0): narrower, usable Preferences

This release addresses user-observed **B01/B02**: Preferences controls and
category navigation were partially clipped when the window was made narrow.
It does not modify the renderer, watcher or idle CPU behavior.

## Changes

- The header `Gtk.Stack` no longer reserves the width of its widest child,
  which previously could force space for all five category tabs even while the
  compact category dropdown was visible.
- Switches to the five-category dropdown below **600sp**, hiding the bottom
  ViewSwitcherBar at the same threshold to avoid cropped tabs. The existing
  dropdown/stack two-way synchronization still selects all five pages.
- At **540sp** and below, the non-essential banner heading is hidden and the
  Discard action uses a shorter label. Both Save and Discard remain available,
  with their existing callbacks and without moving the page content.
- Reduced the unnecessarily fixed minimum width for advanced timing sliders,
  allowing them to use the available space. Their reset and factory-default
  behavior is unchanged.
- Per-monitor palette and artwork controls now wrap within their rows at narrow
  widths, instead of forcing all suffix buttons onto one line.
- Shortened the Preview mode options to *Separate window* / *Pinned in library*.
  Underlying values and the Effect Library selector are unchanged.

## Verification

- Added 7 GTK-free regression tests for the responsive structure, category
  synchronization, banner callbacks, narrow control layout and preview mode.
- All Python source tests passed. GTK/libadwaita could not be launched in this
  environment, so actual Wayland layout, minimum width and accessibility must
  be checked later on GNOME and KDE. This release is **not** a verified runtime fix.
- `./install.sh` was not run on the user's machine.

## Intentionally not changed

- KDE taskbar window grouping (needs a real KDE/Wayland session).
- Per-monitor UI hot-plug refresh (separate observed issue).
- Speculative rendering, memory or idle-CPU optimizations.
