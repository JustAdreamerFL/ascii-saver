# ASCII Saver V89 (0.89.0): editable Photo to ASCII projects

**Date:** 2026-11-08. Experimental/unreleased source build; not verified on KDE/GNOME Wayland.

## Implemented

- **Non-destructive persistence.** `Save as New Artwork` writes a regular
  renderer-compatible `artworks/<name>.txt` and a private, matching folder:
  `photo-projects/<name>/project.json` plus `source.<png|jpg|webp|bmp>`.
  Every new export includes its own copy of the original source bytes and
  all `PhotoSettings` values (crop/fit, dimensions, aspect, tone, palette
  ramp, gamma, edge definition and dithering). The app does not depend on
  the original photo staying in its original location.
- **Discoverable reopen.** Opening a saved project-backed `.txt` in the
  existing Artwork Editor offers **Reopen Photo**. It restores the original
  image and the conversion parameters in the live side-by-side/stacked view.
  Users can create further variants via Save as New, with separate names.
  There is no implicit overwrite of the parent artwork.
- **Respect hand edits.** If text in the existing artwork differs from the
  last generated conversion, reopening the photo shows an explicit notice.
  Manual text changes remain in the original `.txt`; they are not silently
  incorporated into the generated image conversion or discarded.
- **Safe local storage.** Metadata has a fixed versioned schema and references
  only a local bundled source. On load, validate settings, path boundaries,
  file bounds, source checksum and output-text digest. Saves create files
  exclusively without clobbering existing assets and roll back files created
  by an unsuccessful save. Existing plain `.txt` files still work normally.
- **No new runtime dependency.** The project I/O module uses only the Python
  standard library and existing photo conversion logic. The installer now
  installs this module alongside the GTK importer.

## Verification

- New headless tests cover persistent settings/source roundtrip, duplicate-safe
  versions, tampering, manual text edits, invalid input, symlinks and failure
  rollback. Existing photo conversion and old artwork tests remain active.
- The existing GTK file chooser and GdkPixbuf decoder are reused, but they
  have **not** been run on a real GNOME/KDE Wayland desktop in this session.
  Source-level UI contracts are not visual or accessibility test evidence.

## Still open

- Real GNOME/KDE validation of both photo import and project reopening,
  small-window responsive preview, save/discard and manual text interactions.
- Further image filters and local asset searching/filtering.
- Optional licensed online ASCII artwork providers, with offline fallback.
- This release does not provide full layered editing or a replacement for the
  secure desktop lock screen.
