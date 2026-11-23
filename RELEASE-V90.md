# ASCII Saver V90 (0.90.0): local Artwork Studio gallery

**Date:** 2026-11-08. Experimental/unreleased source build; not yet visually tested in GNOME/KDE Wayland.

## Implemented

- **My Artwork** in the native Artwork Editor opens a real offline gallery of `artworks/*.txt` and V89 photo-project-backed text files. The listing displays real ASCII text excerpts as miniature previews, along with the filename, measured cell geometry, landscape/square/portrait orientation, and whether the text has a photo recipe.
- **Browse without changing a document.** Search names/tags, filter by source and shape, or Clear Filters. Open Artwork opens the chosen asset in its own Artwork Editor with its own Save/Discard lifecycle; selection and search never write into another artwork's unsaved buffer. A duplicate click reuses its already-open editor while the gallery is open.
- **Safe, editable tags.** Edit Tags explicitly stores up to 12 labels (maximum 24 characters each), case-insensitively unique. These are written atomically to `artwork-meta/<stem>.json` and never added to the renderer `.txt` format. Bad tag metadata is reported as skipped but a healthy ASCII artwork still appears.
- **Creative template copies.** From Template opens the existing eight-style picker, now with the context-specific **Save a Copy** action. This creates a new, uniquely named artwork via the existing exclusive-create helper. The original template and any other open buffer remain untouched.
- **Bounded and secure.** Index only regular managed `.txt` assets, reject symlinks, skip invalid UTF-8 and assets larger than 2 MB. Preview snippets are limited to 32 lines and 112 columns, with ASCII control characters stripped for safe display. Metadata has a versioned strict schema and a 4 KiB limit.
- The gallery is **offline**, uses current GTK4/libadwaita styling and a breakpoint to stack filters and preview vertically in narrow windows. It does not introduce a network dependency or unsupported color/animated artwork categories.

## Verification

- Headless tests cover cataloguing photo and text artwork, filtering, previews, tag persistence, invalid metadata, file size and symlink protection, and creating distinct editable copies of templates.
- Installer, desktop detection, Python syntax, effect pack and ZIP-integrity checks run as part of release packaging.
- **Not verified:** real GTK resizing, keyboard navigation, screen-reader accessibility, multiwindow focus, Wayland/KWin Task Manager grouping and photo decoding in a live user session. These remain checked as future validation in `TASKS.md`.

## Later milestones

- Explicit author/license provenance, local style labels and reusable conversion presets; only expose color/animation filters if those asset formats are supported.
- Investigate a licensed, safe online ASCII art source with attribution, a permitted import mechanism and graceful offline behavior. No provider has been selected or integrated.
