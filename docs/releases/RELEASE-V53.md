# V53: Modular libadwaita frontend

## Implementation

- Reduced `settings.py` from 1,222 to approximately 190 lines by extracting
  explicit modules for page construction, reusable controls, window shell, gallery view and controller, monitor rules,
  configuration binding and diagnostic actions.
- Converted the general, appearance, monitor and animation boolean controls
  from `Gtk.Switch` inside `Adw.ActionRow` into native `Adw.SwitchRow` rows.
- Dashboard now uses `Adw.PreferencesPage`, which provides responsive margins
  and properly grouped action rows without custom box nesting.
- Introduced `preferences_model.py` for pure, GTK-independent validation.
  Invalid monitor artwork filenames now produce a visible error rather than
  being silently excluded from the saved settings.
- Updated transactional installer to install all new modules.
- Migrated older source-level tests to inspect the modular implementation;
  added explicit module boundaries, native switch-row and model tests.

## Compatibility

- Configuration keys and paths unchanged.
- Rust `ttfx`, Qt6/KIdleTime watcher and binary interfaces unchanged.
- All 37 optimized preview packs unchanged.
- Requires the same PyGObject/GTK4/libadwaita dependencies as V52.

## What remains unverified

No GTK/libadwaita or Wayland runtime is available in the build container.
Please run `python scripts/smoke-adwaita-ui.py` in your CachyOS session before
installing, followed by resizing the five preference pages in the installed app.
