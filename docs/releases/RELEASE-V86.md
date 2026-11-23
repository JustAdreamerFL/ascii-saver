# ASCII Saver V86 (0.86.0): Artwork Studio first milestone increment

**Date:** 2026-11-08. Experimental source build, not a validated desktop release.

## New usable feature

- Existing **Edit Artwork** windows expose **Explore Styles**. The separate searchable
  picker includes eight original, stylistically distinct ASCII samples:
  cinematic horizon, orbital sci-fi, botanical, neon typography, abstract waves,
  pixel skyline, geometric pattern and retro arcade art.
- Every style has a brief explanation and text-art preview. The chooser places
  style choices and preview side by side, then stacks them top to bottom when
  the window is narrower than 690sp.
- **Use Template** replaces only the text currently being edited. If that
  buffer has unsaved edits, the application asks before replacing them. The
  artwork file is **never changed by choosing a template**: Save remains
  explicit, and existing close/discard protection applies.
- The starter templates are bundled offline and need no external libraries,
  web access or changes to `ttfx`.

## Documentation consolidation

- Canonical [ROADMAP.md](../../ROADMAP.md) documents the newly approved Artwork Studio
  milestone, progressive basic-to-advanced UX, adaptive real-time comparison
  requirements and later optional online ASCII catalog search/filter/import.
- [TASKS.md](../../TASKS.md) tracks approved feature work with honest checkboxes.
  [MASTER-BACKLOG.md](../../MASTER-BACKLOG.md) keeps the original issue identifiers.
- Original [UX-ROADMAP.md](../archive/UX-ROADMAP-V54.md) was archived verbatim.
  The root `UX-ROADMAP.md` now directs readers to the canonical roadmap.
- Other historical bug reports, renderer-specific backlogs and dated release
  notes remain in the project, intentionally not flattened into one document.

## Not yet included

- Photo-to-ASCII converter, source/photo + ASCII live comparison, advanced
  image operations, new-asset export flow and online asset gallery.
- No claim that the new template picker is tested on a live GTK/Wayland desktop.

## Verification

- `python3 -m unittest discover -s tests -q`
- `python3 scripts/check-release-assets.py`
- `bash tests/test_installers.sh`
- `bash tests/test_session_detection.sh`
- Python syntax checks and ZIP integrity. Actual GTK/GNOME/KDE review pending.
