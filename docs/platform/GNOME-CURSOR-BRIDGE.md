# GNOME Shell cursor integration (optional)

## Why it exists

GNOME/Mutter owns the pointer when the pointer is over GNOME Shell chrome,
including Dash to Dock. ASCII Saver already sets the documented GTK cursor
`none` for the fullscreen renderer and its VTE child. That only takes effect
while the pointer is over the application's own Wayland surface. It has not
fixed the visible cursor reported on GNOME in V61 through V64.

GNOME Shell 49+ provides `Meta.CursorTracker.inhibit_cursor_visibility()`.
This package includes a **separate, optional extension** for GNOME Shell
49, 50 and 51. The normal ASCII Saver installer never installs/enables this
extension. KDE does not use it. The extension does not interact with KWin or
KScreenLocker and does not modify the secure GNOME lock screen.

## Install only if you explicitly want the GNOME integration

From the extracted source directory while logged into GNOME:

```sh
bash scripts/install-gnome-cursor-bridge.sh
```

GNOME may need a logout/login to discover a newly installed extension on
Wayland. If prompted, log back in, then run:

```sh
gnome-extensions enable ascii-saver-cursor@ascii-saver.local
```

Now use `ascii-saverctl start`. A GNOME-only D-Bus name
`com.github.justadreamerfl.asciisaver.Fullscreen` is held only while ASCII Saver
has a **mapped fullscreen** renderer window. The extension watches the name,
hides the global pointer while it is present, and restores the cursor when
the renderer exits, disconnects, or when the extension is disabled. Windowed
previews never acquire the name. The extension also checks GNOME's screen
shield periodically while the lease is active and restores cursor visibility
if the session is locked even before the app's lock notification is processed.

To remove the optional extension:

```sh
bash scripts/install-gnome-cursor-bridge.sh --remove
```

For diagnostics, run `busctl --user list | grep AsciiSaver.Fullscreen` while
the fullscreen saver is active. A missing name means the GNOME-only lease
was not acquired. This doesn't prove whether pointer focus belongs to the
renderer or GNOME Shell.

## Limitations and verification

- Shell extension is experimental and cannot be tested in this headless build
  environment. Verify GNOME Shell 49–51 behavior, cursor return on input,
  lock/unlock, renderer crash, second-monitor input and extension disable.
- A GNU/Linux Wayland application cannot globally hide the pointer over shell
  actors by calling `Gtk.Widget.set_cursor_from_name('none')` alone.
- Dash to Dock layering is a **separate problem**. This extension hides the
  cursor only; it does not move or disable the dock or bypass a lock screen.
- Installing this extension is explicit and reversible; it is not installed
  or enabled as a side effect of installing/upgrading ASCII Saver.

Reference: https://gjs.guide/extensions/upgrading/gnome-shell-49.html
