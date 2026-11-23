# ASCII Saver 0.61.0 (experimental)

Focus: GNOME UI observations, monitor-count labels and pointer handling.

- Dashboard's Start row now changes immediately between **Start on this display**, **Start on all displays**, and **Start screensaver** as the GDK monitor model changes. No timer or polling is used.
- Displays preferences page immediately updates its connected monitor count on hotplug. Per-monitor editing rows still require reopening Preferences when the physical display list changes; this is tracked as remaining work.
- Fullscreen cursor is hidden again after window mapping and also applied to the realized `GdkSurface`, an attempted mitigation for the GNOME/Mutter pointer. It remains unverified in GNOME.
- GNOME validation backlog documents the Dash to Dock overlap and the Wayland compositor constraint. A normal fullscreen GTK application cannot guarantee a z-order above GNOME Shell overlays.

Testing: offline tests and source validation; GNOME runtime has not been executed in this container.
