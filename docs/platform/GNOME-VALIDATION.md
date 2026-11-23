# GNOME validation backlog

After GNOME native watcher and renderer startup are working, verify:

- ordinary fullscreen windows on Mutter with no `gtk4-layer-shell`: window order, focus, multiple monitors, input dismissal and interaction with native screen locking
- confirm that the selected `org.gnome.ScreenSaver.GetActive` API accurately reports locked and unlocked state, and that `ActiveChanged(true)` immediately removes the visual overlay
- automatic idle startup and unlocking on Fedora Asahi GNOME Wayland
- no interaction with KScreenLocker on GNOME; no KDE dependencies required

This is a **deferred test**, not a claim of compatibility or a scheduled reminder.

## Fedora GNOME observations for V60 (2026-11-02)

- [ ] Fullscreen cursor may remain visible on Mutter Wayland. V61 reapplies the blank cursor at GTK map and at the underlying GDK surface. Confirm actual cursor behavior on GNOME; pointer visibility outside app-owned surfaces remains compositor-controlled.
- [ ] Dash to Dock can remain visible *over* the fullscreen ASCII Saver after lock/unlock if the extension has kept its actor shown. This is **not** a missing `gtk4-layer-shell` package: Mutter does not implement `wlr-layer-shell`, and a normal Wayland client cannot promise to raise above GNOME Shell extension actors. Reproduce both with and without Dash to Dock; investigate an **optional** GNOME Shell extension integration or extension-specific fullscreen/auto-hide setting. Do not secretly disable another extension or modify its settings.
- [ ] Test live monitor hotplug/unplug while the dashboard and preferences are open. V61 labels subscribe to GdkDisplay's items-changed signal, without polling. Future improvement: dynamically add/remove *per-monitor configuration rows*, preserving unsaved and disconnected monitor settings.
- [ ] After core GNOME screensaver works, explicitly test regular fullscreen window stacking, focus, input dismissal and GNOME locking without Layer Shell.

## V62 verification after V61 unsuccessful cursor mitigation

- [ ] Cursor is hidden on the fullscreen surface without moving the mouse.
- [ ] Cursor remains hidden on entering/returning to a fullscreen surface.
- [ ] Cursor is visible in windowed previews and immediately after fullscreen exits.
- [ ] Compare cursor and dock behavior with Dash to Dock enabled vs temporarily disabled by the user, particularly after lock/unlock.
- [ ] If the pointer is visible only over the dock, record that GNOME Shell,
      not ASCII Saver, has pointer focus there. No unsupported global hiding.

## V63 remaining Wayland cursor and overlay diagnostics

- V61 and V62 attempted `Gdk.Cursor.new_from_name("none")` and surface/device cursor overrides, but the user still reports a visible pointer on GNOME/Mutter.
- Confirm whether `/proc/$PID/exe` corresponds to the current installed watcher using **System Information** or `ascii-saverctl components`, then separately identify whether the visible cursor is inside the renderer's surface or belongs to GNOME Shell/Dash to Dock.
- Do not claim fullscreen windows can override GNOME Shell extensions or bypass secure lock-screen layering.
- After basic GNOME functions are verified, retest regular fullscreen fallback without layer-shell, especially post-lock/unlock and Dash to Dock overlay.

## V64 opt-in Dash to Dock settings

- [ ] `ascii-saverctl dock status` reports system/user-local schema keys without side effects.
- [ ] In a GNOME user session, optionally run `dock apply`, launch normal fullscreen saver, and check that the dock autohides. This changes dock preferences globally until `dock restore`.
- [ ] Confirm the dock doesn't appear during a transition between effects or while holding the final frame.
- [ ] Confirm normal GNOME lock screen wins over ASCII Saver and dock settings are unaffected by lock/unlock.
- [ ] Run `dock restore`, inspect original settings and confirm other fullscreen applications behave as before.
- [ ] If Dash to Dock stays visible after unlock despite correct settings, track extension-specific bug separately; do not attempt unsafe window stacking.

## V65 cursor correction and new optional bridge (not runtime-tested)

The user clarified that the mouse pointer **is visible on GNOME**. Previous
V64 release notes incorrectly said it was not. V65 packages an opt-in GNOME
Shell 49–51 extension using Meta.CursorTracker.inhibit_cursor_visibility().
A GNOME-only fullscreen renderer announces its mapped state via a session
D-Bus name and releases ownership when quitting or locking. GNOME Shell
restores visibility automatically on owner disappearance, including crashes.

Test explicitly on real GNOME (extension opt-in, normal GUI unaffected):

- [ ] Cursor invisible as soon as fullscreen saver maps, over artwork and dock
- [ ] Cursor returns on mouse movement, keyboard escape, renderer quit/crash
- [ ] Cursor remains visible in windowed preview, main GUI and preferences
- [ ] Cursor returned before/during GNOME lock and after unlocking
- [ ] All monitors and optional Dash to Dock extension behave correctly
- [ ] Disabling/removing bridge leaves pointer visible normally

No live Mutter/GNOME Shell session was available in the build environment.
