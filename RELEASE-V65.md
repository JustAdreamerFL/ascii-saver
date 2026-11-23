# ASCII Saver 0.65.0: GNOME pointer visibility correction

The earlier V64 notes incorrectly stated that the mouse cursor was already
hidden on GNOME. The user explicitly reports that **it remains visible**.

V65 introduces an optional GNOME Shell 49+ cursor bridge for the case in which
GNOME Shell or Dash to Dock controls cursor visibility outside the GTK fullscreen
surface. The existing GTK4 `none` cursor remains the default; this bridge is
opt-in and independent of the dock compatibility settings from V64.

- GNOME fullscreen renderer publishes a session D-Bus lease *only while mapped*.
- Extension watches lease ownership, uses Mutter's cursor visibility API and
  restores the pointer on name disappearance, screen lock or disable.
- Windowed preview and KDE never publish the lease.
- Extension is manually installed via `scripts/install-gnome-cursor-bridge.sh`;
  it is not silently enabled by `install.sh`.
- All other screensaver components are carried forward from V64.

See `GNOME-CURSOR-BRIDGE.md` for installation and testing instructions.

**GNOME behavior remains unverified until tested in a live GNOME Shell session.**
