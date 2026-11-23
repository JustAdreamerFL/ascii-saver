# KDE ASCII Saver GUI: GNOME HIG and libadwaita implementation

V52 is a first substantial native libadwaita refactor of the **control GUI**.
The screensaver rendering overlay itself intentionally remains GTK4 + VTE and
the KDE idle watcher remains C++/Qt6. Neither has a libadwaita equivalent.

## Design decisions

- **Navigation:** five named preference categories with `Adw.ViewStack`,
  `Adw.ViewSwitcher`, `Adw.ViewSwitcherBar`, and `Adw.Breakpoint`. The latter
  puts navigation at the bottom for narrower windows. HIG recommends 3–5 views
  for switchers and bottom navigation when the header is too narrow.
- **Preferences:** native `Adw.PreferencesPage`, `Adw.PreferencesGroup` and
  `Adw.ActionRow` replace the large label/control grids. Control descriptions
  now appear below their labels rather than exclusively as tooltips. Native
  `Adw.ExpanderRow` groups advanced controls.
- **Independent displays:** the same switches, color pickers and spin controls
  are retained and become visible only with independent monitor settings.
- **Playlist editor:** `Adw.NavigationSplitView` supports split sidebar/content
  at wide sizes and a navigable single page on narrow sizes. `Adw.EntryRow` and
  `Adw.SwitchRow` replace plain name and enable/shuffle controls.
- **Other windows:** the library, effect live preview and performance monitor
  use `Adw.Window`, `Adw.ToolbarView` and `Adw.HeaderBar`; the main dashboard
  uses Adwaita groups for controls.
- **Feedback:** pending Save/Discard is a persistent overlay, not a transient
  toast, since it represents ongoing unsaved state. Brief action results also
  use `Adw.ToastOverlay`. Detailed diagnostics remain readable in the page.
- **Specialized widgets:** keep `Gtk.FontDialogButton`, `Gtk.ColorDialogButton`,
  scales, `Gtk.DrawingArea` graphs, VTE terminals and animation textures because
  libadwaita does not have direct replacements for these.

## HIG / API references consulted

- <https://developer.gnome.org/hig/> (general design)
- <https://developer.gnome.org/hig/patterns/nav/view-switchers.html>
- <https://developer.gnome.org/hig/guidelines/adaptive.html>
- <https://developer.gnome.org/hig/patterns/feedback/toasts.html>
- <https://developer.gnome.org/hig/patterns/controls/buttons.html>
- <https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.7/class.PreferencesPage.html>
- <https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.7/class.PreferencesGroup.html>
- <https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.7/class.NavigationSplitView.html>

`Adw.PreferencesWindow` has been deprecated since libadwaita 1.6, and
`Adw.PreferencesDialog` (1.5+) is preferred for a dialog. This application
needs a separate persistent preferences **window** with user-requested view
switching, so we use `Adw.ApplicationWindow` containing the nondeprecated
`Adw.PreferencesPage` and related widgets instead of `PreferencesWindow`.

## Verification limits

Offline syntax and Python unit tests do not validate GTK widget allocation or
GObject Introspection bindings. Run `python scripts/smoke-adwaita-ui.py` on a
machine with GTK4/libadwaita installed, then inspect each view at wide/narrow
window sizes. Check accessibility focus and keyboard shortcuts manually.

## Future architecture cleanup

`settings.py` still coordinates application settings, preview lifecycle,
playlist integration and the preferences model. Next steps include extracting
page controllers and a typed observable settings model, and revisiting gallery
cards with Adwaita presentation patterns while preserving viewport-aware
preview decoding and low memory use.
