# ASCII Saver V91 (0.91.0): creative looks and reusable Photo to ASCII presets

**Date:** 2026-11-08. Experimental/unreleased source build. Real GTK/GNOME/KDE/Wayland behavior remains unverified.

## Implemented

- A curated set of **six distinct built-in styles**: Classic Terminal,
  Film Noir, Soft Horizon, Graphic Ink, 8-Bit Arcade, and Architectural Detail.
  These are actual conversion settings with different character mappings,
  tonal treatment, canvas geometry, edge handling and optional dithering,
  not empty templates or cosmetic labels.
- The visible **Start with a creative look** combo + Apply Look button
  populates the existing controls. It recomputes the existing side-by-side or
  stacked live preview without saving, replacing an editor buffer or changing
  the input photo. Users can then fine-tune all controls.
- **My conversion presets** is collapsed by default for progressive disclosure.
  Save Preset copies the currently visible basic and advanced settings into a
  named personal preset; selecting a saved look re-applies it. Remove requires
  explicit confirmation and is unavailable for immutable built-in presets.
- Personal data resides under XDG configuration `photo-presets/*.json` with
  a strict versioned format, input bounds, safe directory checks, no symbolic
  link following, exclusive creation, rollback after failed writes, and no
  unprompted overwrites. Duplicate display names are rejected. Broken files
  are skipped while built-in looks continue to work.
- The `.txt` renderer output, existing photo-project recipe format and all
  photo-to-ASCII basic/advanced controls stay backward compatible.

## Files

- `photo_presets.py`: GTK-independent built-in recipes and verified storage.
- `photo_ascii_view.py`: discoverable Apply Look and collapsed personal manager.
- `install.sh`: installs the new module.
- `tests/test_v91_photo_presets.py`: built-in coverage, storage roundtrips,
  file corruption/traversal/symlink protection, rollback, and UI wiring.
- Updated `TASKS.md`, `ROADMAP.md`, `MASTER-BACKLOG.md`, `README.md`,
  `CHANGELOG.md`, `VERSION` and `build_info.py`.

## Verification limitations

Automated and headless tests verify the settings, code paths, storage, errors
and installer contents. They do not confirm the actual visual rendering,
keyboard navigation, narrow-screen layout, input accessibility, or GTK/KWin
window behavior. Those are separately tracked in TASKS.md.

## Next

Optional further image processing and local artist/license metadata, then
research permitted third-party ASCII galleries. Online browsing remains
unimplemented and is not represented by an inactive control.
