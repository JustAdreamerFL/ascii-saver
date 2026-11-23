# V52 - libadwaita control UI overhaul

## Implemented

- Shared `adwaita_ui.py` with native preferences pages, groups and action rows.
- Replaced the legacy two-column `Gtk.Frame`/`Gtk.Grid` preference settings
  with `Adw.PreferencesPage`/`Adw.PreferencesGroup`/`Adw.ActionRow`.
- Preserved the five adaptive categories, and existing Save/Discard behavior.
- Changed raw playlist JSON and advanced timing to `Adw.ExpanderRow`.
- Updated display-specific controls to native Adwaita rows and descriptions.
- Added an `Adw.ToastOverlay` for short save/action feedback.
- Converted Effect Library, live preview, measured durations and performance
  windows to `Adw.Window` with `Adw.ToolbarView` and `Adw.HeaderBar`.
- Converted the Playlist Editor to `Adw.ApplicationWindow` and responsive
  `Adw.NavigationSplitView`, plus `Adw.EntryRow` and `Adw.SwitchRow`.
- Restructured the small dashboard into grouped Adwaita actions.
- Shipped the new shared UI helper in the installer.
- Added offline architecture checks and a manual GTK construction smoke test.

## Compatibility

The Rust `ttfx` engine, KDE C++ idle watcher, saved configuration format,
artwork files and 37 optimized previews are unchanged from V51. The installer
keeps the previous settings and builds the same engine.

## Tests

- Python suite: 169 tests, 1 skipped (GTK/PyGObject not installed in build environment).
- Python compilation, shell syntax and asset checks: passed.
- Requires live GTK/libadwaita testing on CachyOS; compiled GUI and window
  layout are **not** runtime verified here.

## Manual QA

After installing, run `python scripts/smoke-adwaita-ui.py` from the unpacked
source, then open Preferences, resize below 780sp, test all five pages,
Save/Discard, independent display settings, gallery previews, playlist editor,
and return to wide window layout. Report GI exceptions with tracebacks.
