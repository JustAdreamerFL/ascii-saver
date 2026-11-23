# ASCII Saver V83 (0.83.0): full issue history and compact status display

Date: 2026-11-07 (experimental source build; live KDE/GNOME test pending).

## Changes

- Recover all original user-observed issues from `OBSERVATIONS-COMBINED.md`, `BACKLOG-V55.md`, `RENDERER-BACKLOG.md` and `UX-ROADMAP.md` in a full, cross-referenced `MASTER-BACKLOG.md`.
- Keep `TASKS.md` as the short source-level checklist, now linking to the full backlog. Separate historical proposals from approved priorities and live-only validation.
- A05: fix unbounded watcher/renderer label width in the Dashboard and Preferences. Long status strings are single-line and ellipsized rather than wrapped, with full content available via tooltip and selection. No change to control behavior or the status model.
- Add regression tests for both UI components and updated release docs.

## Verification and limitations

Headless Python unit tests, installer tests, preview pack/assets checks and syntax checks are performed for the source artifact. Source-level contracts do **not** verify GTK layout allocation, actual Wayland window behavior, or the Rust `ttfx` runtime. See `TASKS.md` and `MASTER-BACKLOG.md` for outstanding integration tests.
