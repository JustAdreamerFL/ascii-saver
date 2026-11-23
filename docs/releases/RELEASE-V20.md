# Experimental V20: Embedded effect preview

- Effect play buttons now open a single inline VTE terminal under the effects grid, rather than opening many separate windows.
- Stop preview destroys the terminal and cancels pending launches; selecting a different effect replaces the active preview.
- The preview uses the installed Rust ttfx and configured artwork, capped at 30 FPS.
- Normal saver and playlist scheduling remain independent of previews.

Limitations: This is an on-demand animated preview panel, not 37 simultaneous animated thumbnails. KDE Wayland and GTK/VTE runtime have not been tested in this container. The archive is experimental.
