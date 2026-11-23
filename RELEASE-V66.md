# ASCII Saver 0.66.0: pointer-hidden fullscreen without GNOME Shell extension

## Why this version exists

The user verified the following behavior on GNOME Wayland (Fedora):

- Plain GTK4 fullscreen with `cursor=none`: pointer hidden over GTK content.
- VTE terminal widget with `cursor=none`: text-selection I-beam remains visible.
- VTE placed under a full-area `Gtk.DrawingArea` in `Gtk.Overlay`, with
  `set_can_target(True)` and `cursor=none`: I-beam **not visible** and
  `Gtk.EventControllerMotion` **receives mouse motion**.

## Changes

- Fullscreen `SaverWindow` now uses `Gtk.Overlay`, with VTE as its main child
  and a targetable, transparent `Gtk.DrawingArea` covering all of it.
- Invisible cursor is applied to window, VTE, overlay, catcher, and GDK surface
  before presentation and on mapping / pointer entry.
- Root capture-phase keyboard and pointer controllers continue dismissing
  the fullscreen saver on user activity, without treating `enter` as motion.
- Windowed/persistent preview continues using bare VTE; it does not use
  the input overlay and retains the normal pointer.
- GNOME Shell cursor extension lease is **off by default** even when the
  extension is installed. For diagnosis, setting
  `ASCII_SAVER_GNOME_CURSOR_BRIDGE=1` explicitly reenables the legacy lease.
- No mouse warp, pointer constraint, global cursor control, automatic
  change of GNOME extensions, or lock-screen bypass.

## GNOME test matrix

Use the real application on GNOME Wayland with the cursor bridge disabled:

1. `ascii-saverctl start` with the pointer initially over text. It should be
   invisible immediately. Move the pointer and confirm immediate dismissal.
2. Let the idle watcher start fullscreen and repeat the same check.
3. Repeat on both monitors, including portrait/landscape as applicable.
4. Open `ascii-saverctl preview` and confirm preview stays open while pointer
   is visible and can be moved normally.
5. Check `Escape` or another key dismisses the real fullscreen saver.
6. Leave pointer stationary at start and verify the saver does not dismiss
   merely because the pointer enters the newly mapped window.

### Known limitation

GTK cannot guarantee global cursor concealment over GNOME Shell surfaces such
as Dash to Dock if the shell itself takes pointer focus. The saver should
normally dismiss on movement before this becomes noticeable. Real GNOME
compositor validation is required to confirm the overlay behavior in app.

### Testing status

Source/packaging tests can run without GTK. The user's **isolated** GTK/VTE
overlay test passed, but the actual 0.66.0 app has not yet been run on GNOME.
