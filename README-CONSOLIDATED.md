# ASCII Saver, consolidated experimental source

This source tree combines the user-provided ASCII Saver source (with activity protection) and V15 ttfx patches. It is NOT a production-validated Plasma build.

## Install

Run `bash install.sh` as a regular desktop user. The installer builds the native KDE/KF6 watcher and the **bundled, modified Rust `ttfx` renderer**, requiring `cargo`, `rustc`, CMake, Qt6, KF6IdleTime, GTK4 and VTE4 development/runtime components. The installer proposes platform-specific dependency commands where supported. After installing, open ASCII Saver from the application menu or run `ascii-saverctl prefs`.

## Remove

`~/.local/bin/ascii-saverctl uninstall`

Your personal settings and artwork are preserved by default. KWin activity-inhibitor scripts may require separate inspection/removal.

## Source integrity and limitations

The project includes MIT-licensed original ASCII Saver components and bundled modified Rust ttfx source, with relevant upstream notices. This is an experimental build, not yet fully integration-tested on every supported desktop. Native KScreenLocker wallpaper/animation rendering remains unfinished. Rendering-frame FPS is not necessarily display-presented FPS. GPU engine activity via DRM fdinfo is not a measure of whole-GPU utilization. Activity protection depends on native KDE/KWin integration and is experimental.

## Next consolidation update: performance graph accuracy

The performance window now separates CPU and memory plots with independent units,
filters by monitor, and does not merge measurements from unrelated monitors into
a single connected curve. Effect-completion events are excluded from resource
aggregation while remaining available for measured duration summaries.

This is instrumentation for the `ttfx` child processes, not comprehensive GPU
usage or composited frame timing. No new claims about GPU or FPS are made.

## V17 final-frame retention

After each successful ttfx effect, the app redraws the selected per-monitor
ASCII artwork into its VTE terminal and holds that static image until the
coordinated transition. This makes the hold independent of ttfx terminal
cleanup behavior. Note: the redraw uses the original artwork rather than the
final animation's special styling; wide Unicode glyph alignment and exact
palette fidelity still need testing in KDE.

The new pure-Python `final_frame.py` has four unit tests. These checks do not
verify the VTE/Wayland rendering path.

## V18: cell-aware final artwork retention

Final artwork centering now uses Unicode terminal cell widths rather than Python
string length. This improves CJK/wide-character logos, clipping, and combining
marks during the synchronized hold. The renderer remains dependent on GTK/VTE
for live tests. Grapheme clusters with emoji ZWJ or terminal-specific ambiguous
width rules may still differ.

Animation speed is still adjusted through ttfx's frame-rate setting. A truly
independent duration scale (without dropping frames or changing effect timing)
requires renderer-level support and is **not** claimed as implemented here.

## V45 installer hotfix

See [RELEASE-V45.md](RELEASE-V45.md) for the Rust `E0308` fix and validation steps.

### V47 gallery memory notes

Effect and playlist thumbnails are preprocessed into `preview-packs/*.aspr` and
installed under `effects/`. They use `Gdk.MemoryTexture` rather than runtime
GIF decoders or Glycin. Only scroll-visible cards have active timers and open
pack readers. The library releases all textures when closed.
Run `python scripts/build-preview-packs.py` if modifying the original GIFs;
this developer-only step requires Pillow, but the installed application does not.
See `RELEASE-V47.md` for details.

### V51 preferences navigation

Run `ascii-saverctl prefs` for the separate libadwaita Preferences window, or open the app dashboard with the desktop launcher. Preferences pages are General, Appearance, Displays, Animations and Preview. Navigation switches from header tabs to a bottom bar on narrower windows. Requires `libadwaita` and its Python GObject introspection typelib.


### Native GNOME support (V57)

On GNOME/Fedora the installer compiles a small C/GIO watcher instead of the
Plasma Qt6/KIdleTime watcher, so Qt/KDE development packages are not required.
Install `gcc`, `pkgconf-pkg-config`, `glib2-devel`, and `json-glib-devel` for
building the daemon, plus the existing GTK4/VTE/libadwaita dependencies.

Run `./install.sh --detect-session` to see the detected desktop, window manager/compositor and idle watcher. Run `./install.sh --check` to verify dependencies automatically for that session
and `./install.sh` to install. The native watcher uses Mutter IdleMonitor via
session D-Bus and GNOME SessionManager idle inhibitors. It has not been
live-tested on GNOME; refer to RELEASE-V57.md for testing and limitations.

### Desktop and compositor detection (V58)

No backend variable is required for normal installation. `./install.sh` and
`./install.sh --check` use the desktop session metadata in
`XDG_CURRENT_DESKTOP` (ordered, colon-separated), `XDG_SESSION_DESKTOP`, and
`DESKTOP_SESSION`, with a limited running-process fallback for missing session
metadata. `./install.sh --detect-session` prints the detected desktop,
Wayland/X11 session type, compositor/window manager, and selected watcher
without building or installing anything.

| Session | Idle watcher | Dependencies |
|---|---|---|
| KDE Plasma / KWin | C++ / Qt6 / KF6 KIdleTime | Qt6 and KIdleTime development headers |
| GNOME / Mutter | C / GLib/GIO / Mutter IdleMonitor | GLib and Json-GLib development headers |
| Sway, Hyprland, niri, COSMIC, other unsupported sessions | Not implemented | Installer stops safely and reports unsupported desktop |

A recognized XDG session overrides running-process guesses, since multiple
compositors can exist under one user account. The process fallback is
best-effort, not a guaranteed detection of the current session. Backend
selection may be overridden with `KDE_ASCII_SAVER_BACKEND=kde` or `gnome` for
troubleshooting, but this does **not** provide support for other compositors.


### 0.60.0 clean-identity behavior

ASCII Saver does not import or delete files, services, artwork, or caches under
`kde-ascii-saver`. If that older application is installed on the same machine,
uninstall it separately before installing ASCII Saver to avoid two idle watchers.
The legacy V55 uninstaller retains its settings/art and does not clear
`~/.cache/kde-ascii-saver`; remove that specific cache directory manually if desired.

Edit Artwork in Preferences > General opens a built-in libadwaita editor;
terminal-based CLI editors are no longer launched from a captured subprocess
in that UI.

## Primary menu and component versions (V63)

The dashboard menu follows GNOME HIG and contains Preferences, Keyboard Shortcuts, Help, About and Quit. The separate **System Information** view distinguishes the running GUI build, installed release, Rust `ttfx` version, native watcher version and selected desktop backend. A running watcher built from an older binary is reported as **Restart required**.

You can retrieve the same report without GTK using `ascii-saverctl components`; the watcher supports `ascii-saver-watcher --version` without starting the idle service. Standard shortcuts include `Ctrl+,`, `Ctrl+?`, `F1`, `F10`, `Ctrl+W` and `Ctrl+Q`.

GNOME Shell's Dash to Dock overlay can still appear above an ordinary fullscreen
Wayland window, especially after unlock. On GNOME, run `ascii-saverctl dock status`
to inspect fullscreen-related dock settings; `dock apply` explicitly enables a
reversible, global fullscreen-hiding profile, and `dock restore` returns to the
previous configuration. No settings are changed automatically by installation.
See [GNOME dock compatibility](GNOME-DOCK-COMPAT.md) for limits and security.
The current pointer behavior should be verified separately; cursor mitigation
is not part of this release.
