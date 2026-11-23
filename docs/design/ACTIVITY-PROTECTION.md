# Activity protection (experimental)

Preferences contains two independently configurable switches:

- **Respect app activity inhibitors** (on by default): consult PowerDevil active inhibition list. Applicable to media players, browsers, presentations and games that request inhibition.
- **Protect fullscreen apps and games** (on by default): optional KWin 6 script reports foreground fullscreen state to the idle watcher via session D-Bus. No window names or application titles are transferred.

The fullscreen KWin helper is installed on supported systems with `kpackagetool6`, enabled with `kwriteconfig6`, and reloaded with `qdbus6`. KDE may require manually enabling it in System Settings > Window Management > KWin Scripts or relogging. If the helper is absent, the fullscreen switch has no effect. Application inhibitors work independently. A video playing in a non-fullscreen game that does not inhibit may still be missed.

This does **not** change KScreenLocker, system idle lock policies or PowerDevil's configuration. Manual Start and Preview are not inhibited.

Installation: `bash install.sh`. Removal: `kde-ascii-saverctl uninstall`. The user configuration is retained, and the optional KWin script is disabled/removed. Testing requires KDE Plasma 6 Wayland because CI cannot verify KWin script signal availability or D-Bus delivery.
