# ASCII Saver V96 (0.96.0): manual retouch inside Artwork Studio

**Date:** 2026-11-08. Cumulative experimental source release.

## What changed

The existing native Artwork Editor has a **Retouch** popover. Basic text
editing remains available without opening any tools. For more directed edits,
place the text caret on the target cell, choose a single ASCII ink using the
input field or the compact palette, then press **Paint at Caret**. Paint
replaces the existing character or inserts just before a line break if the
caret is at the end of a row. **Erase** turns an existing character into a
space and cannot extend the row.

To change a larger shape, select the relevant text region and press **Mirror
Selection** or **Flip Selection**. Mirror reverses line content and adjusts the
orientation of `/`, `\`, `<`, `>`, parentheses and brackets. Short rows
receive spaces to maintain rectangular alignment; Flip reverses selected rows.
Both preserve the selected fragment's terminating newline, if present.

All actions use the existing unsaved GTK text buffer. The new **Undo/Redo**
buttons use a bounded native Gtk.TextBuffer history (80 levels), with retouch
edits grouped as one undo step. Save remains explicit and the existing
unsaved-changes prompts remain in effect. The original photograph, photo
project recipe and online cache are never modified by retouching.

## Scope and limitations

The new tools are **caret-based**. Mouse-drag painting, rectangle-selection
handles, non-ASCII display-width editing, pixel-grid retouch, layers, and
per-artwork animation or color editing are **not** being claimed. Native
GTK/Wayland rendering, keyboard focus and compact-window popover fit still need
to be checked on an actual GNOME/KDE desktop. Legacy ASCII artworks remain
readable with no migration required.

## Verification

Headless Python tests include ASCII validation and control-character rejection,
painting/erasing at line endings, selected text transforms, large-region
limits, explicit save safety and structural GTK wiring. Run the complete
Python regression suite, compileall, installer and session detection checks,
37 effect asset checks, and ZIP integrity validation.

Rust renderer rebuild and real GTK/Wayland tests are not possible here.
