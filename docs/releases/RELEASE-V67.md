# ASCII Saver 0.67.0: reliable fullscreen keyboard dismissal

## What changed

In V66 `Gtk.Application.set_accels_for_action("app.quit", ["Escape"])`
referenced a nonexistent application action. The window capture-phase key
controller still handled normal key events, but the accelerator was not a
working fallback. V67 registers the action and routes activation through the
existing idempotent `quit_saver()` shutdown path. The Escape accelerator only
exists for fullscreen saver mode; windowed previews are intentionally
persistent when users type or move the pointer.

For KDE/wlroots compositors that support gtk4-layer-shell, V66 constructed
all monitor surfaces with `Gtk4LayerShell.KeyboardMode.NONE` and only
promoted the first display to `EXCLUSIVE` after the window was presented.
V67 asks for `EXCLUSIVE` on the primary monitor **before the first map**;
secondary monitors start with `NONE`. Monitor hotplug still refreshes the
single keyboard-owning surface.

The transparent VTE pointer overlay introduced in V66 is unchanged.

## Test on your desktop

1. Install with `./install.sh`, then run `ascii-saverctl components` to
   verify GUI/installed components report 0.67.0.
2. Run `ascii-saverctl start` on GNOME Wayland. Without moving the pointer,
   press **Escape** immediately. The fullscreen saver should close.
3. Start again and press another key. It should close too. Start once more
   and move the pointer; the saver should close without showing a VTE I-beam.
4. Run `ascii-saverctl preview`. Move the pointer and press **Escape**.
   The regular decorated preview should stay open; close it using the window
   close button or `ascii-saverctl stop`.
5. On a two-monitor KDE Plasma Wayland session, repeat with one portrait and
   one landscape display. Test after disconnecting/reconnecting one display.
6. Verify lock-screen handoff still closes the visual saver and never covers
   the system's secure lock screen.

## Verification already completed

- Python source suite: 248 tests run, 247 passed, 1 skipped (GTK/Gio unavailable).
- Installer shell tests and packaged preview/asset checks passed.
- Python compile checks passed.

## Not verified here

There is no GTK4/VTE runtime, compositor, or Cargo toolchain in this build
environment. Actual Wayland focus delivery, fullscreen overlay behavior and
Rust engine execution still require the desktop tests above.
