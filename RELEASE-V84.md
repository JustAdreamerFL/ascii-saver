# ASCII Saver V84 (0.84.0): KDE window identity source corrections

Date: 2026-11-07. Experimental source build; **KDE Wayland grouping is not verified**.

## User-reported issue (E02/B213)

The Playlist Editor showed a generic Wayland taskbar icon instead of grouping with ASCII Saver; the Effect Library was visible in the window overview but missing in the KDE Task Manager.

## Implementation

- The Playlist Editor no longer launches a second `Adw.Application` / Python process with `io.github.robbybobby77.AsciiSaver.Playlists`. The main `SettingsApplication` owns and reuses a genuine `Adw.ApplicationWindow` for playlist editing. Both editor and dashboard therefore inherit the installed `io.github.robbybobby77.AsciiSaver` application ID.
- The direct `playlist_editor.py` entry point forwards `--playlist-editor` to the registered ASCII Saver application instead of registering an ungrouped new identity.
- Effect Library is an independent `Adw.ApplicationWindow` associated with the same parent `Gtk.Application`, rather than an `Adw.Window(transient_for=Preferences)` that KWin may deliberately omit from the Task Manager.
- Keep one editor per app instance. Closing the playlist editor releases any live PTY preview, animated thumbnails and timers, then refreshes only the saved playlist data in still-open Preferences, preserving unrelated unsaved settings.
- The Effect Library retains its own Save/Discard controls and hides on close. Preferences still destroys its library on close; other application windows stay independent.
- Add GTK-free tests for app ownership, repeated opens, close/reopen lifecycle, preview cleanup, and compatibility with V74 independent save/discard.

## Validation and limitations

Offline Python unit tests, syntax, installer/session detection and effect preview assets checked as recorded in verification output. **Window identity is fixed in source, not verified on KDE Wayland**. KWin taskbar grouping and whether the Effect Library appears in the Task Manager require a real Plasma session; GNOME likewise awaits runtime UI verification. No claim of a measured performance gain or a completed compositor-level fix.
