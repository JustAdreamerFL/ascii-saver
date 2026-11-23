# ASCII Saver 0.64.0 (GNOME dock compatibility controls)

**Source:** V63. Rust renderer and native KDE/GNOME watcher sources unchanged.

- Adds read-only `ascii-saverctl dock status` for the GNOME Dash to Dock schema
  and its fullscreen-hiding settings. It detects system or user-local schemas.
- Adds explicitly invoked `ascii-saverctl dock apply` and `dock restore`.
  Applying writes a reversible backup before editing settings; it does **not**
  disable an extension or silently change GNOME settings on installation.
- Restoring does not override manual settings changes made after the profile
  was applied.
- Adds six unit tests for defaults, reversible changes, interrupted/repeated
  application behavior, and preserving newer user settings.
- The current compositor rule is unchanged: KDE uses Gtk4LayerShell overlay;
  GNOME uses ordinary fullscreen. GNOME Shell/Dash to Dock may still draw above
  that window, especially after lock/unlock. This profile improves the
  extension's intended fullscreen behavior but is **not a compositor fix**.
- No new cursor changes. The user's current observation is that the pointer
  was not displayed; the remaining issue was the dock/overlay.

## Verification

Python tests and package checks can run offline. Actual GNOME/Mutter, Dash to
Dock and post-lock behavior still require a live GNOME session. Secure lock
surfaces must never be overdrawn.
