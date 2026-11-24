# ASCII Saver

> **V115 (experimental, 2026-11-24):** Preferences now has an **Idle watcher** switch that starts or stops the watcher and enables or disables automatic startup for your user. Packaged autostart is reported correctly even when a stale development systemd unit exists. See [RELEASE-V115.md](docs/releases/RELEASE-V115.md).

> **V114 (experimental, 2026-11-24):** Fixes opening Preferences from the packaged application by importing the missing `adaptive_action_row` helper used by the effect library. See [RELEASE-V114.md](docs/releases/RELEASE-V114.md).

> **V113.0 (experimental, 2026-11-24):** Fixes starting the screensaver from a system package by resolving `/usr/bin/ascii-saver` and `/usr/bin/ascii-saver-settings` instead of leftover per-user launcher paths. See [RELEASE-V113.0.md](docs/releases/RELEASE-V113.0.md).

> **V112 (experimental, 2026-11-24):** The online installer now installs the matching Debian, Fedora or Arch package through the system package manager, with `--source` available for development installs. Release notes highlight the newest package for each distribution and collapse older Fedora builds. See [RELEASE-V112.md](docs/releases/RELEASE-V112.md).

> **V111 (experimental, 2026-11-23):** Native Debian, Fedora and Arch packages are published with the source archives, using system Python/GTK and prebuilt watchers/ttfx, with no venv or Cargo required on the installed system. The manual Release workflow now builds and publishes all artifacts together. See [RELEASE-V111.md](docs/releases/RELEASE-V111.md).

> **V110 (experimental, 2026-11-23):** Application identity is now `com.github.justadreamerfl.asciisaver` across GTK, desktop entries, AppStream metadata, icons and the fullscreen cursor bridge. Upgrades remove files from the previous identity while preserving configuration and artwork. The online installer and release workflow target `JustAdreamerFL/ascii-saver`. See [RELEASE-V110.md](docs/releases/RELEASE-V110.md).

> **V109 (experimental, 2026-11-09):** Appearance now allows turning off **Override effect RGB colors** so Rust animations retain their own ANSI/RGB output; the setting is saved and used in all preview paths. Preferences has a real labeled sidebar on wide windows and a compact selector on narrow ones. Timing sliders take full-width rows. All editing and diagnostics tools are inside Preferences > Tools. The editor shows both Text and Draw, and the shared window-shortcut handler captures Esc/Ctrl+W/Ctrl+Q before focused child controls. Effect Library pinned preview receives a vertically centered host. Headless tests pass; real GNOME/KDE Wayland GUI confirmation still needed. See [RELEASE-V109.md](docs/releases/RELEASE-V109.md).

> **V108 (experimental, 2026-11-09):** Stability/UX corrections from direct Fedora feedback. Global and per-display palettes now support Add/Remove/Reset (1–8 colors), and per-display colors can be enabled independently. My Artwork has **Recently used** (records new playback from V108), Draw supports click and freehand drag with selected-text painting, and Online Surprise Me explicitly selects its chosen artwork in the loaded preview list. Windowed Preview is a titled Adwaita window with Esc/Ctrl+W/Ctrl+Q, tool windows have closing shortcuts, Effect Library is transient to Preferences, its inline preview is centered and gallery filters have wider, centered choices. Clean-state Preferences footer remains hidden. These features passed headless tests; **real GTK/Wayland interactive testing is still required**. See [RELEASE-V108.md](docs/releases/RELEASE-V108.md).

> **V107 (experimental, 2026-11-09):** Rebuilt Preferences after the V106 Fedora screenshot. Removed width-forcing header tabs and in-Preferences status/diagnostic cards; all five sections use one compact selector, all wide controls stack under their labels, advanced palette transitions are collapsed, and the clean “Changes saved” footer is hidden. Diagnostics, graphs, measurement history and editing are reachable through the main window's **Tools** menu. Source tests pass; real GNOME/KDE GTK visual confirmation is pending. See [RELEASE-V107.md](docs/releases/RELEASE-V107.md).

> **V106 (experimental, 2026-11-09):** Fixes based on real Fedora feedback: single native Close control in Help/System Information, same desktop identity for Preview, automatic multi-color palette cycling with explicit Static override, and narrow Preferences rows that stack labels/controls instead of clipping. Save/Discard now stays in a stable bottom tray. All changes are headless tested; GNOME/KDE GUI confirmation remains open. See [RELEASE-V106.md](docs/releases/RELEASE-V106.md).

> **V104 (experimental, 2026-11-08):** Synchronized fullscreen monitor
> cohort launches. One shared callback starts all monitors for the next
> effect/palette round; round-aware hotplug timers cannot restart a removed
> display or run in the wrong round. Standalone Preview and V103 palettes are
> preserved. Simulation tests passed, real KDE/GNOME Wayland testing is still
> pending. See [RELEASE-V104.md](docs/releases/RELEASE-V104.md).

ASCII-art terminal-effect screensaver for Linux desktops, with native idle
integration for KDE Plasma/KWin and GNOME/Mutter. The fullscreen renderer is
GTK4/VTE with a modified Rust `ttfx` binary;
the settings dashboard uses GTK4/libadwaita. A native idle watcher is built
for the detected desktop backend.

This is an experimental release. Fullscreen/desktop stacking and lock-screen
integration depend on the compositor. ASCII Saver does not replace or cover
the secure desktop lock screen. GNOME Shell extensions such as Dash to Dock
can appear above normal fullscreen Wayland windows.

## Repository layout

| Path | Contents |
|---|---|
| `src/` | GTK/VTE renderer, dashboard, preferences and pure Python helpers |
| `native/kde/` | Qt 6/KF6 idle watcher and its CMake build |
| `native/gnome/` | GNOME/Mutter GIO idle watcher |
| `data/` | Desktop entries, metainfo, icon and systemd units |
| `integrations/` | Optional GNOME Shell and KWin helper extensions |
| `debian/` | Debian/Ubuntu packaging metadata |
| `packaging/` | Shared package payload, Fedora spec and Arch PKGBUILD |
| `bin/` | Installed launcher scripts |
| `config/` | Default user configuration and logo |
| `docs/` | Architecture, installation, platform, design, planning and release notes |
| `tests/` | Offline unit and source-contract tests |
| `scripts/` | Maintenance, preview-pack and smoke-test helpers |
| `preview-packs/` | Packed effect preview assets |
| `ttfx-rust/` | Instrumented Rust terminal-effects renderer |

Run the offline suite with `python3 -m unittest discover -s tests -q` and the
full source/installer checks with `./verify-build.sh`.

See [current checked task list](TASKS.md),
[active Artwork Studio roadmap](ROADMAP.md),
[indexed historical backlog](MASTER-BACKLOG.md),
[historical V85 priorities](docs/planning/PRIORITIES-V85.md),
[V85 responsive galleries](docs/releases/RELEASE-V85.md),
[V84 release details](docs/releases/RELEASE-V84.md),
[V82 release details](docs/releases/RELEASE-V82.md),
[historical V81 priorities](docs/planning/PRIORITIES-V81.md),
[V81 single preview selector and release history](docs/releases/RELEASE-V81.md),
[V80 hot-plug monitor preferences](docs/releases/RELEASE-V80.md),
[V79 adaptive Preferences](docs/releases/RELEASE-V79.md),
[V78 diagnostics and artwork editing](docs/releases/RELEASE-V78.md),
[V77 preview usability](docs/releases/RELEASE-V77.md),
[V76 performance graphs and measured durations](docs/releases/RELEASE-V76.md),
[V75 gallery-first Playlist Editor](docs/releases/RELEASE-V75.md),
[V74 contextual Save/Discard changes](docs/releases/RELEASE-V74.md),
[V73 preview final-frame fixes](docs/releases/RELEASE-V73.md),
[V72 palette-matched thumbnails](docs/releases/RELEASE-V72.md),
[V71 authoritative palette notes](docs/releases/RELEASE-V71.md),
[V69 mixed-monitor auto-fit notes](docs/releases/RELEASE-V69.md),
[V68 playback reliability notes](docs/releases/RELEASE-V68.md),
[V67 keyboard dismissal validation](docs/releases/RELEASE-V67.md),
[full details](docs/releases/README-CONSOLIDATED.md),
[GNOME dock compatibility](docs/platform/GNOME-DOCK-COMPAT.md), and the
[optional GNOME cursor bridge](docs/platform/GNOME-CURSOR-BRIDGE.md).

**V90 local Artwork Library (extended in V92):** Choose **My Artwork** from the built-in Artwork Editor to browse saved `.txt` art and project-backed images with ASCII thumbnail previews, source and shape filters, searchable filename/tags, and Open Artwork in a separate editor. Details writes optional private tags, creator, description, license and source metadata rather than modifying renderer files; From Template / Save a Copy creates a new user asset from one of eight original styles. Local gallery is offline-ready; an optional V92 Browse Online fetches ascii-bin community art with search, filters, safe previews, cached offline fallback and source/license warnings. Rights to individual remote artworks are NOT verified. GUI tests on GNOME/KDE Wayland remain open. See [RELEASE-V90.md](docs/releases/RELEASE-V90.md) and [ROADMAP.md](ROADMAP.md).

**V100 Canvas work area:** In Draw on Canvas, choose **Work area**
for an expandable grid up to 200 x 100 character cells, or **Fit to artwork**
to discard only unused workspace. The `.txt` file is not padded until the
user actually draws into previously empty cells. Large artworks are drawn
using only the visible scroll viewport and an extra guard cell, reducing
unnecessary text-layout work during scrolling. These are source-tested
features; on-device GTK/KDE/GNOME validation remains open. See
[RELEASE-V100.md](docs/releases/RELEASE-V100.md).

**V99 Canvas keyboard editing:** In Draw on Canvas, use the arrow keys to
move a highlighted cell, Space to paint the selected ASCII glyph and
Delete/Backspace to erase. The cursor is scrolled into view and its position
is shown in the existing hint line. Undo/Redo and explicit Save are shared
with mouse painting and Text mode. Canvas edits now update only changed text,
not the entire document, and redraw after the grouped edit completes. GTK
keyboard and Wayland scrolling remain unverified; see [RELEASE-V99.md](docs/releases/RELEASE-V99.md).

**V98 Canvas interaction:** Canvas mode offers 75%-200% zoom, a cosmetic
Grid switch and responsive tool groups that wrap on narrow windows. Pango
measures logical character-cell sizes for both pointer hit testing and drawing,
with scroll position approximately preserved when zoom changes. After clicking
the canvas, Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y use the shared Undo/Redo history.
Neither zoom nor grid visibility changes the saved art. Actual GNOME/KDE
fractional-scale and GTK interaction testing remains outstanding; see
[RELEASE-V98.md](docs/releases/RELEASE-V98.md).

**V97 Draw on Canvas:** Artwork Editor now has an optional mouse-driven
character grid for brush and eraser strokes. Quick motion is interpolated;
one drag is one Undo step in the same editable text buffer. Toggle back to
Text for keyboard editing or Unicode artwork. This experimental source
feature still needs live GTK/GNOME/KDE validation; see [RELEASE-V97.md](docs/releases/RELEASE-V97.md).

**V96 manual artwork retouch:** The native Artwork Editor now has a small
**Retouch** toolbar popover with a one-character ink brush and eraser at the
text caret, plus horizontal Mirror Selection and vertical Flip Selection.
Its native bounded Undo/Redo history and the existing explicit Save protect
unfinished edits. It is not yet a mouse-driven pixel canvas or layered editor.
Real GTK keyboard/focus testing remains pending; see [RELEASE-V96.md](docs/releases/RELEASE-V96.md).

**V95 online artwork discovery:** Browse Online shows up to 48 remote
ASCII cards at once, with Show More, title/size sorting, and a Surprise Me
shuffle that reorders the already downloaded artwork to inspire exploration.
Online refresh cannot overlap itself, and a transient error preserves the
items already loaded in the window. Local art and imported attribution are
unchanged. See [RELEASE-V95.md](docs/releases/RELEASE-V95.md); remote network and GTK/Wayland
end-to-end testing remain pending.

**V94 custom character ramps:** Select **Custom** in the Photo to ASCII
style menu to reveal a safe dark-to-light character ramp under Advanced.
Enter 2–63 unique printable ASCII characters; a space for white highlights
is appended automatically. It renders in the live comparison and survives
preset saving and editable photo projects. Incorrect ramps prevent export
and clear stale preview text. Older projects and built-in styles remain
unchanged. See [RELEASE-V94.md](docs/releases/RELEASE-V94.md); live GTK/VTE testing pending.

**V93 photo finishing:** Advanced Photo to ASCII now supports optional posterization into 2–8 tone bands and configurable white/gray/black backdrops for transparent pixels. Both work in the same live preview and are preserved in photo projects and personal presets; older recipes load with original default settings. [RELEASE-V93.md](docs/releases/RELEASE-V93.md) has details and test limitations.

**V87–V89 Artwork Studio: Photo to ASCII.** The existing native artwork editor now offers a Photo to ASCII workflow with locally imported PNG/JPEG/WebP/BMP images, adjustable monochrome conversion, character aspect compensation and responsive original/output comparison. Explicit Save as New Artwork creates a duplicate-safe `.txt` in the local artwork collection; Use in Editor respects unsaved changes. This is source-tested; GTK/GNOME/KDE validation remains pending. V88 adds collapsed Advanced controls for gamma, edge definition and dithering with a neutral-default Reset; live GTK tests remain pending. V89 now stores the original photo plus conversion recipe alongside every newly exported `.txt` artwork. Existing artwork with a project can be reopened for non-destructive adjustments and Save as New exports another variant; live GUI testing remains pending. See [RELEASE-V89.md](docs/releases/RELEASE-V89.md), [RELEASE-V88.md](docs/releases/RELEASE-V88.md), [RELEASE-V87.md](docs/releases/RELEASE-V87.md) and [ROADMAP.md](ROADMAP.md).

**V85 responsive gallery UX:** Effect Library cards adapt to one, two or three columns instead of forcing a fixed three-column width. On narrow windows the filters and preview actions stack, and both libraries offer Clear filters when a search has no matches. Saved and unsaved selections are unaffected. Real GTK/Wayland visual validation is still pending. See `RELEASE-V85.md`.

**V84 KDE taskbar source correction:** Effect Library and Playlist Editor now use separate application-owned GTK windows with the installed ASCII Saver desktop ID, rather than a transient library dialog and another Playlists process. Runtime KWin verification is still pending. See `RELEASE-V84.md`.

**V81 preview-control ownership:** The Effect Library Play mode is now selected in the Effect Library window only; its save format and library Save/Discard behavior are preserved. The main changelog includes a chronological history of releases with surviving notes. See `RELEASE-V81.md`.

**V80 live monitor preferences:** Display FPS, palette and artwork controls are reconciled on monitor plug/unplug without losing unsaved edits or persisted settings of disconnected displays. See `RELEASE-V80.md`.

**V79 adaptive Preferences:** Compact category navigation no longer reserves the width of the five full-size tabs; banner actions and monitor controls adapt to narrow windows. See `RELEASE-V79.md`.

**V78 diagnostics and artwork:** The Run Diagnostics action opens a dedicated, read-only Adwaita window with pass/fail rows, copy, rerun and clear controls. Closing the native artwork editor now distinguishes a completed save, an unchanged file and discarded unsaved edits. See `RELEASE-V78.md`.

**V77 preview usability:** Effect Library and Playlist Editor single-effect previews now center the renderer canvas, while the separate window provides its own Replay action. Duplicate Close/help controls were removed, pinned previews are taller, and an Effect Library thumbnail toggles that effect without launching playback. See `RELEASE-V77.md`.

**V76 measured performance:** native grouped summaries by display, a distinct
shared GTK/VTE category, independent chart scales with legends, real event
markers for measured FPS, and clearer measured-duration labels. See `RELEASE-V76.md`.

**V75 Playlist Editor:** the animated effect gallery is now the primary,
expanding editor area, with search and selected-effect counts. Current playlist
options and automatic generation are collapsed and independently scrollable so
they cannot consume the main preview gallery. See `RELEASE-V75.md`.

**V74 workflow fixes:** Effect Library and Playlist Editor now have their own
Save/Discard banners. Closing the playlist editor updates just the
playlist form, preserving other unsaved Preferences changes. See `RELEASE-V74.md`.

**V73 preview completion:** Both live Effect Library preview modes now keep their final rendered artwork without a trailing linefeed or restored text cursor. A failed temporary statistics-file cleanup no longer blocks fullscreen monitor synchronization.

**V72 color-aware effect thumbnails:** Effect Library and Playlist Editor sample animations use the first selected palette color and background. Changing global color swatches in Preferences immediately re-tints open library animations, before saving. The 37 preview packs contain precomputed grayscale masks for fast recoloring without Pillow or launching the Rust renderer. Per-monitor settings and playlist-cycle transitions are not represented by these generic sample cards.

## Installation

```sh
./install.sh
```

The installer identifies the current KDE or GNOME session, checks dependencies,
compiles the native watcher and the bundled Rust `ttfx` engine, and stages files
under the user's home directory. User preferences and artwork are retained.

## Controls

```sh
ascii-saver                 # main Dashboard GUI
ascii-saver preferences     # open Preferences directly
ascii-saver playlist        # Playlist Editor
ascii-saver start           # fullscreen screensaver (background)
ascii-saver preview         # persistent resizable preview
ascii-saver stop            # stop currently running renderer
ascii-saver status          # renderer and watcher status
ascii-saver doctor          # installation diagnostics
ascii-saver components      # running GUI/installed/watcher versions
ascii-saver --help          # unified command help
ascii-saver play --once     # direct foreground renderer, one effect
ascii-saver dock status     # GNOME: inspect Dash to Dock (read-only)
```

The older entry points remain available: `ascii-saverctl start`,
`ascii-saverctl prefs`, and `ascii-saver-settings` (opens Preferences).
Help and System Information are dismissible with **Esc** or **Close**.
If upgrading a running GTK GUI instance, fully close the old GUI process
first so the D-Bus-registered instance reloads the new Python code.

A dock profile is **not** applied by installing or starting ASCII Saver, and
cannot force GNOME Shell to stack behind normal windows. Its changes are
global to the user's Dash to Dock until restored.

## GNOME cursor on fullscreen screensaver

V66 uses a full-area transparent GTK4 overlay over the VTE renderer in the
fullscreen saver. The overlay owns the invisible pointer, preventing VTE's
text-selection I-beam from showing. This does **not** require a GNOME Shell
extension. Windowed previews keep their normal cursor. The earlier optional
cursor bridge is retained only for explicit fallback diagnostics and is
**disabled by default**, even when installed. Remove the old extension with
`scripts/install-gnome-cursor-bridge.sh --remove` if you no longer need it.

A regular Wayland window cannot hide the cursor while GNOME Shell owns pointer
focus, for example over Dash to Dock. See [V66 testing and limitations](docs/releases/RELEASE-V66.md).

## Project issue tracking

- [Short checked TASKS checklist](TASKS.md)
- [Full historical MASTER-BACKLOG register](MASTER-BACKLOG.md), reconciled with the original observations, V55 backlog, renderer backlog and UX roadmap
- [Dated CHANGELOG](CHANGELOG.md) and [V85 release notes](docs/releases/RELEASE-V85.md)

The checkbox status means source implementation only; unverified KDE/GNOME Wayland behavior is tracked separately.

### Product roadmap and artwork creation (V86)

[ROADMAP.md](ROADMAP.md) is the active UX and milestone plan.
[TASKS.md](TASKS.md) tracks implemented versus outstanding work, while
[MASTER-BACKLOG.md](MASTER-BACKLOG.md) keeps original bug reports and decisions.
The older UX roadmap is retained in `docs/archive/UX-ROADMAP-V54.md`.

Edit Artwork now includes **Explore Styles**, an offline picker of eight
creative, fully editable ASCII starters. Search and preview are built in;
the template preview changes from side by side to stacked on narrow windows.
Choosing a template changes only the editor buffer, not the artwork file until
Save. Photo to ASCII and the first collapsed Advanced controls are implemented
in source, but not yet validated in the live GTK desktop. Persistent photo recipes and local asset browsing were added in V89-V90;
V92 introduced optional online browsing. Additional online providers remain
a future milestone and must respect provenance and per-artwork rights.

### Artwork Studio: creative conversion looks (V91)

Photo to ASCII now offers six built-in starting looks alongside the editable
Basic and Advanced controls. The optional My conversion presets panel can
store the entire conversion recipe locally for reuse. Applying a look changes
only the current preview, not the original image or an existing `.txt` artwork.
Custom recipes reside in `photo-presets/` with validated JSON files and no
network access; saved photo projects from V89/V90 remain readable. See
[ROADMAP.md](ROADMAP.md) for outstanding milestones and GNOME/KDE validation.

### Artwork Studio: online collection and artwork attribution (V92)

In **My Artwork**, choose **Browse Online** to load the publicly available
[ascii-bin](https://github.com/amwhoi/ascii-bin) collection (opt-in network
request), filter its text artworks, preview them side by side or stacked, and
**Import a Copy**. Imported files have no execution privileges and do not
replace existing artwork. A last successful collection is cached for offline
browsing. Local work does not depend on the online provider.

**Rights notice:** ascii-bin labels its compilation CC0 but explains that
some works are collected from authors it does not control. The app records
this warning, the source URL, and an unknown creator, not an invented author
or a claim of verified commercial-use permission. Check rights independently
before redistribution or commercial use. Metadata is stored separately from
renderer-compatible `.txt` files.

V92 code was tested offline with a representative provider-format fixture;
actual network availability and GTK/Wayland UI behavior remain to be tested.

### V96 manual artwork retouch

In the native Artwork Editor, open **Retouch** to paint/erase one ASCII cell at
its caret, mirror/flip selected lines, or undo/redo changes. No file is saved
until you press **Save**; the default text editor remains fully available.
The mouse-drawing canvas was introduced later in V97 and refined through
V100; this V96 description is retained as historical release context.


V103: Optional ping-pong palette progression (first → last → first) with existing per-monitor overrides and synchronized effect rounds. Desktop validation pending. See RELEASE-V103.md.
