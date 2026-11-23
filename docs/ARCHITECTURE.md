# ASCII Saver: application architecture (V53)

The screensaver still uses **Python + GTK4/libadwaita** for its user interface,
**Rust `ttfx`** for the actual effect renderer, and **C++/Qt6/KIdleTime** for
native KDE idle detection. The V53 restructuring does **not** replace either
of the native components, change the user's configuration file, or install a
new desktop service.

## UI boundaries

| Module | Responsibility |
|---|---|
| `settings.py` | Application entry point and lightweight composition of windows. |
| `preferences_shell.py` | ViewStack, adaptive view switchers, unsaved-changes banner, header navigation. |
| `preferences_controls.py` | Constructs preference controls and monitor-specific inputs without laying out pages. |
| `preferences_pages.py` | Places controls in native Adw pages and groups for General, Appearance, Displays, Animations and Preview. |
| `preferences_gallery_view.py` | Builds the Effect Library window, animated cards, filters and dedicated preview container. |
| `preferences_gallery.py` | Lazy thumbnail playback, live preview process lifetime and library controller actions. |
| `preferences_displays.py` | Monitor-specific control visibility and font-fit diagnostics. |
| `preferences_state.py` | GTK control bindings, compare-with-saved state, save/discard and loading from disk. |
| `preferences_model.py` | **GTK-independent** validation of playlist JSON, color, font, excluded effects, and monitor artwork filenames. |
| `preferences_actions.py` | Background commands, diagnostics, durations and performance windows. |
| `effect_catalog.py` | Effect names used by the gallery; the renderer maintains its own list. |
| `adwaita_ui.py` | Small shared builders for native `Adw.PreferencesPage`, `Adw.PreferencesGroup`, `Adw.ActionRow`. |

`SettingsWindow` composes these pieces using small mixins. An individual module
owns one part of the application. GTK widgets are still used where libadwaita
provides no suitable specialized replacement (font/color choosers, VTE terminal,
animated previews and time-series graphs).

### Startup and save path

1. `SettingsApplication.open_preferences()` creates a `SettingsWindow`.
2. Window calls UI builders in their declared order; all signals are connected
   only after the full widget tree exists.
3. `PreferenceStateMixin._load_preferences()` loads the user's configuration.
4. When controls change, a snapshot is compared to the last saved snapshot.
   Reverting a change dismisses the unsaved-changes banner.
5. On Save, `preferences_model.validate_form()` validates free-form inputs before
   `ctl.update_config_values()` persists values. Errors do not overwrite disk.
6. The C++ watcher and Rust renderer continue reading the established config
   and unchanged runtime paths.

### GNOME HIG / libadwaita decisions

- Preferences use native `Adw.PreferencesPage` + `Adw.PreferencesGroup` and
  labeled rows, instead of arbitrary tables and nested frames.
- Boolean preferences are `Adw.SwitchRow` (title, explanatory subtitle,
  whole-row activation); independent monitor options are revealed only when
  that mode is active.
- Navigation has five flat sections, adapting between an `Adw.ViewSwitcher`
  and an `Adw.ViewSwitcherBar` as the window narrows.
- Persistent unsaved state uses a non-reflowing overlay with Save/Discard,
  rather than a transient toast. Short action feedback can use `Adw.ToastOverlay`.
- Dedicated effect browsing and playlist editing remain separate windows
  because their content is complex; playback remains unaffected by moving the mouse.

Official design references:
- [GNOME HIG navigation](https://developer.gnome.org/hig/guidelines/navigation.html)
- [GNOME HIG](https://developer.gnome.org/hig/)
- [Libadwaita PreferencesPage](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/class.PreferencesPage.html)
- [Libadwaita PreferencesGroup](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/class.PreferencesGroup.html)

## Validation and limitations

Run from the extracted archive:

```sh
python -m unittest discover -s tests -q
python scripts/check-release-assets.py
python scripts/smoke-adwaita-ui.py  # requires a live GTK/libadwaita desktop
```

The offline tests exercise persistence rules and architectural source
contracts, but **cannot verify actual GTK allocation or Wayland behavior**.
The application still needs on-device tests for resizing, gallery preview
memory usage, palette transitions, monitor fitting and KScreenLocker.

## GNOME backend (V57)

On KDE Plasma the Qt6/KIdleTime C++ watcher remains unchanged. On GNOME the
installer builds `gnome_idle_watcher.c` using GLib, GIO, and Json-GLib: it
subscribes to Mutter IdleMonitor D-Bus events and runs a GMainLoop while idle.
The native daemon starts the same GTK/VTE Python rendering application when
Mutter signals that the configured idle delay elapsed. The daemon itself does
not import Python or load the GTK interface. GNOME-specific `IsInhibited`
checks suppress launch during normal session idle inhibitors.

This uses an *optional* Mutter API and is not guaranteed to work on every
GNOME version. GNOME compositor behavior and default lock-screen controls
remain authoritative. See `RELEASE-V57.md` for dependencies and test status.
