# GNOME Dash to Dock and ASCII Saver fullscreen

This note applies to **GNOME Shell/Mutter Wayland**, not KDE Plasma/KWin.

GNOME Shell extensions can draw their own actors above ordinary Wayland
windows. Mutter does **not** support `wlr-layer-shell` for external clients,
so ASCII Saver cannot promise to appear above Dash to Dock, the GNOME overview,
Shell notifications, or the secure lock screen. On KDE Wayland, ASCII Saver
already requests the `OVERLAY` layer. Its normal windowed preview does not.

## Opt-in compatibility profile

Dash to Dock has an existing fullscreen/autohide policy. The following command
checks the relevant keys without modifying your GNOME configuration:

```sh
ascii-saverctl dock status
```

For a user who explicitly wants the dock to auto-hide around fullscreen
windows, the following **optional** command changes some global Dash to Dock
preferences. It first writes a backup under `~/.config/ascii-saver/`:

```sh
ascii-saverctl dock apply
```

It sets only supported keys:

- `dock-fixed = false`
- `autohide = true`
- `intellihide = true`
- `intellihide-mode = ALL_WINDOWS`
- `autohide-in-fullscreen = false`

These settings are *global*, so they also affect other fullscreen apps until
restored. They do **not** disable GNOME extensions. On an installation lacking
the Dash to Dock schema, nothing changes. Some versions of Ubuntu Dock reuse
the same schema. Installation never applies these changes automatically.

Return to your original preferences with:

```sh
ascii-saverctl dock restore
```

A restore does not override keys that the user changed after applying the
profile; those keys remain in the backup for manual inspection or later
restoration. If the desired preferences are already set, apply does nothing.

## Known limitations

- Dash to Dock may temporarily remain visible after unlocking GNOME even when
  its auto-hide options are enabled. This is an extension behavior outside the
  renderer's control. The compatibility profile **cannot guarantee** a fix.
- GNOME Shell overlays and secure lock surfaces always take precedence over a
  normal screensaver. ASCII Saver intentionally quits on native lock
  activation, never tries to cover the password prompt, and never installs a
  privileged Shell component.
- If you want to diagnose a persistent dock after unlock, test whether it
  disappears when the user manually enters and leaves GNOME Overview, and
  whether the behavior happens with the extension disabled manually.
- For a guaranteed compositor-level solution GNOME Shell extension support
  would be needed, with an explicit separate opt-in and GNOME version testing.

Sources:
- https://github.com/micheleg/dash-to-dock/blob/master/schemas/org.gnome.shell.extensions.dash-to-dock.gschema.xml
- https://wayland.app/protocols/wlr-layer-shell-unstable-v1
