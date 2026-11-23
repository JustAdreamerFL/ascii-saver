# ASCII Saver V105 (0.105.0)

## Preferences, unified commands and keyboard dialogs

Fixes user-reported behavior from V103/V104 on Fedora, targeting the exact
preferences window construction failure and the confusing command entry points.

### Changes

1. **Preferences startup:** `ShellBuilderMixin._make_navigation()` referenced
   `banner_label` and `banner_discard`, which were locals of `_make_shell()`.
   This raised `NameError` while constructing the Preferences window, leaving
   an incomplete GUI in the application switcher. The two controls are now
   retained as `self.banner_label` and `self.banner_discard` across both
   methods. A regression test checks this concrete failure.
2. **Window routing:** `SettingsApplication.do_command_line()` does not
   activate and present the Dashboard before handling `--preferences` or
   `--playlist-editor`. Direct requests target only their intended window,
   including a request forwarded to an existing application instance.
3. **Unified CLI:** The single `cli.py` dispatcher, installed through
   `ascii-saver`, `ascii-saverctl` and `ascii-saver-settings`, supports:
   `ascii-saver` (Dashboard); `ascii-saver preferences` (Preferences);
   `ascii-saver playlist`; `ascii-saver start|preview|stop|status|doctor`;
   `ascii-saver play` (foreground renderer); `ascii-saver --help` and
   `--version`. The compatibility wrappers `ascii-saverctl prefs` and
   `ascii-saver-settings` still open Preferences. Legacy `--windowed` and
   `--once` remain supported for the direct renderer. The `app.py --help`
   description no longer describes the app as KDE-only.
4. **Playback routing:** The control command explicitly invokes
   `ascii-saver play` for fullscreen and Preview renderer startup. Without
   this change, the new dashboard-first launcher would prevent the old
   `ascii-saverctl start` from starting the renderer.
5. **Desktop launcher:** The `.desktop` app entry opens the main dashboard;
   the installed Preferences launcher opens Preferences directly.
6. **Help and System Information:** The two auxiliary windows are now
   modal, transient Adwaita dialogs, support Escape to close, and have a
   visible Close button. The shared dialog builder also improves the fallback
   Keyboard Shortcuts window.

### Command examples

```sh
ascii-saver                 # Main Dashboard
ascii-saver preferences     # Preferences directly
ascii-saver playlist        # Playlist Editor
ascii-saver start           # Fullscreen (background)
ascii-saver preview         # Windowed Preview
ascii-saver stop            # Stop current renderer
ascii-saver status          # Process and watcher status
ascii-saver --help          # Unified commands and options
ascii-saverctl prefs        # Compatibility alias
ascii-saver-settings        # Compatibility alias (Preferences)
```

### Verification

- 606 Python unit tests (605 passed, 1 skipped), including 13 new V105
  tests covering command routing, installed entry points, static GUI
  regressions and GTK application dispatch without importing GTK.
- Installer and desktop-session detection shell tests: PASS.
- All 37 effect preview packs and installer payloads: PASS.
- Python compileall and shell syntax: PASS.
- ZIP archive verified after packaging, and all V104 files retained.

**Limitations:** This environment does not include PyGObject/GTK/libadwaita
or a real GNOME/KDE Wayland session, so the actual Preferences window,
Help/System Information Escape behavior, Alt-Tab/taskbar behavior and native
Rust renderer must be tested on the user's Fedora/desktop after installation.
The source bug is verified; graphical behavior is not yet confirmed.

### Suggested on-device validation

1. Close the previously running ASCII Saver graphical app before testing;
   a registered running GUI process keeps its old Python code until exit.
2. Upgrade using the existing `./install.sh` workflow; settings and art remain
   under the user's config directory.
3. Run `ascii-saver --version`, `ascii-saver`, `ascii-saver preferences`,
   `ascii-saver-settings`, and `ascii-saverctl prefs` in a terminal.
4. Open Help (F1) and System Information (main menu), press Esc and confirm
   the dialog closes while the main window stays open. Try Preferences on both
   GNOME and KDE if available.
5. Run `ascii-saver preview`, then `ascii-saver stop`, and verify
   `ascii-saver status` reports the expected mode.

No user configuration migrations are necessary.
