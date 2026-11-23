# ASCII Saver 0.62.0 (GNOME cursor follow-up)

The GTK4 fullscreen cursor mitigation in V61 did not work in the Fedora
GNOME/Mutter test. V62 uses GTK4's documented named `none` cursor, attaches
realize/map handlers **before** presenting the fullscreen window, and applies
the cursor to the root GTK widget, VTE child, GDK surface, and default pointer
device. It reasserts the cursor on pointer-enter without polling or cursor
warping. The normal windowed preview keeps its ordinary pointer.

**Important:** A GNOME Shell overlay (including Dash to Dock) is outside the
ASCII Saver Wayland client's surface. This change cannot hide the pointer
while an overlay owns pointer focus, nor forcibly stack fullscreen windows
above shell extension actors. That requires separate GNOME Shell integration
or correcting the extension's behavior. Do not disable extensions silently.

Static regression tests pass, but we cannot run Mutter and GTK4 in the build
environment. User validation on GNOME is required before claiming success.
