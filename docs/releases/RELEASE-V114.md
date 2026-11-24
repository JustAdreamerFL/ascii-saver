# ASCII Saver V114 (0.114.0) | Preferences fix

**Date:** 2026-11-24.

## Fix

Opening Preferences could abort while constructing the window because
`preferences_gallery_view.py` used `adaptive_action_row` from `adwaita_ui`
without importing it. The view now imports the helper, and a regression test
checks that the symbol is both imported and used.

## Validation

- Preferences was opened under a virtual X display from an installed package
  layout and remained running without traceback.
- All 687 offline tests pass.
