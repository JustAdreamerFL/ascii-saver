# KDE ASCII Saver V51 (experimental)

## Main window and adaptive libadwaita preferences

- Small, separate control dashboard (Start Now, Preview, Stop, Preferences, Effect Library, Playlist Editor).
- Actual libadwaita `Adw.ApplicationWindow` preference pages: General, Appearance, Displays, Animations and Preview.
- Adaptive `Adw.ViewSwitcher`: header tabs on wide windows, bottom tabs below a 780sp breakpoint.
- Existing controls and manual Save/Discard banner preserved. Category content scrolls independently.
- `kde-ascii-saverctl prefs` and the desktop Settings launcher open Preferences, including when the GTK application is already running.
- Preview window remains open while the library closes. Closing the main dashboard closes Preferences and its preview children.
- Embedded preview is reopened with any Play button or the new `Replay last effect` button.
- New dependency: `libadwaita` / Adw introspection typelib. Installer checks for it and offers package guidance.

## Verification limits

Python, shell and source-level regression tests are run in the container. It does not have PyGObject/GTK/Adw, Qt or a live KDE session. The adaptive layout and child-window lifecycle still need runtime verification on the user's CachyOS desktop. The modified Rust renderer source is unchanged from V50.
