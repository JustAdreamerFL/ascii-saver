# Changelog

ASCII Saver release history, newest first. Experimental source-level fixes still require GNOME/KDE runtime validation. Detailed notes and verification limitations are in the corresponding `RELEASE-Vxx.md` files.

**Historical dates:** These are development milestones reconstructed from dated project conversations and surviving release notes, not claims that every experimental version was publicly published on that date. The label `(estimated)` means the day is approximate. V22 and V30 have no surviving release-note entries and have not been invented.


## [Unreleased]

## 0.114.0 (experimental) - 2026-11-24
- Fix the Preferences window failing to construct with a `NameError` caused by
  the effect library view not importing `adaptive_action_row`.

## 0.113.0 (experimental) - 2026-11-24
- Fix the packaged controller resolving launchers under `~/.local/bin` instead
  of the system `/usr/bin` paths. Starting the screensaver from the installed
  package now works.

## 0.112.0 (experimental) - 2026-11-24
- Make `install-online.sh` the default native user installer: detect the
  distribution/release/architecture, verify the matching package from
  `SHA256SUMS`, and install it with `apt`, `dnf` or `pacman`. The previous
  user-local build is available with `--source`.
- Let the Release workflow choose Debian, Fedora and Arch image tags, defaulting
  each package build to the newest available distribution image.
- Resolve the current Fedora release from `fedora:latest` and automatically build
  the previous release for the expandable release-notes section.
- Generate release notes from the published assets, highlighting the newest
  Debian, Fedora and Arch packages and collapsing older Fedora builds.

## 0.111.0 (experimental) - 2026-11-23
- Add native Debian, Fedora and Arch packages with prebuilt watchers and ttfx.
- Consolidate package builds into the manual Release workflow so source
  archives, packages and checksums publish together.
- Package installations use system Python/GTK and do not create a virtual
  environment or require Cargo on the installed machine.

## 0.110.0 (experimental) - 2026-11-23
- Rename the application identity to `com.github.justadreamerfl.asciisaver`, including desktop entries, AppStream metadata, icon names and the fullscreen cursor D-Bus name. Upgrades remove the previous desktop-identity files while preserving user configuration and artwork.
- Point the online installer and project links at the current repository and publish through the manual GitHub Release workflow.

## 0.109.0 (experimental) - 2026-11-09
- Add an explicit opt-out from V70's forced palette over effect-generated RGB; persist it in saved config and use it consistently for fullscreen, Preview, and both Effect Library preview modes. The configured foreground remains a terminal fallback with the override off.
- Provide truly adaptive Preferences navigation: compact header category DropDown on narrow windows and a synchronized labeled sidebar at desktop widths, retaining all six categories. Reflow sliders to full rows, with clear current value, no cramped horizontal breakpoint.
- Move all six Tools into a Preferences Tools page, remove duplicate tool actions from the main menu/dashboard, and keep an explicit Library preview-mode preference.
- Capture Esc/Ctrl+W/Ctrl+Q at the window level for Preferences, Playlist Editor, Artwork Editor and transient tools, with editor close-request confirmation preserved; add clear Text/Draw editor mode controls, and permit single-column Unicode box-drawing artwork in Draw mode.
- Center inline Effect Library VTE vertically within its bounded preview viewport without taking away card scroll space.
- Add 20 V109 headless tests and retire obsolete source-only layout assertions. Live GNOME/KDE GTK visual validation remains outstanding; see [RELEASE-V109.md](docs/releases/RELEASE-V109.md).


## 0.108.0 (experimental) - 2026-11-09
- Stabilize palette editing: 1–8 editable swatches with Add/Remove/Reset, live reset-state affordance and independent per-display palettes separate from per-display FPS or artwork. Preserve backward-compatible saved JSON and explicit static/cycle modes.
- Add private, bounded recently played artwork history, populated when the renderer actually starts, and expose the default artwork in My Artwork. Start recording history with V108 rather than guessing older usage.
- Make artwork editing more direct: Draw opens by default for compatible artwork; mouse clicks and freehand drags paint cells; selected text can be painted or erased in one buffer action with Undo/Redo. Live pointer precision remains unverified.
- Make online Surprise Me choose and visibly select a matching artwork even when the new choice was beyond the loaded first page; update its preview.
- Use an Adwaita window and proper title for persistent Preview with Esc/Ctrl+W/Ctrl+Q. Add close shortcuts to transient tools. Keep Effect Library transient to Preferences, center its inline preview and clean up its renderer on close.
- Center filter dropdown labels via GTK list-item factories; permit sensible filter width; trim redundant labels and keep clean Preferences footer hidden.
- Add 25 headless V108 tests; update superseded source-test expectations without discarding actual behavior tests. **Live GTK/GNOME/KDE GUI validation remains necessary**.
- See [RELEASE-V108.md](docs/releases/RELEASE-V108.md).

## 0.107.0 (experimental) - 2026-11-09
- Replace five compressed Preferences navigation tabs with one always-visible category selector in the libadwaita HeaderBar. All five categories, direct navigation and keyboard access remain.
- Prevent the narrow-window clipping shown in Fedora screenshots by stacking all specialized control rows vertically by default, including per-display FPS, palette and artwork widgets. Avoid relying on GTK breakpoints after a wide child has already raised the window minimum size.
- Return General to editable activation settings only. Move renderer/watcher statuses to the main Dashboard and move diagnostics, performance graphs, measured effect timings and artwork editing into the app's Tools menu.
- Collapse advanced palette transition controls, remove the permanent “Changes saved” footer and use toasts for actions. Save/Discard remains a bottom action bar only when the configuration is dirty.
- Remove a duplicate native Close in the System Diagnostics window, retain Esc. Update legacy source contracts to assert the replacement design and add V107 regression tests. Live GTK/GNOME/KDE sizing remains unverified.
- See [RELEASE-V107.md](docs/releases/RELEASE-V107.md).

## 0.106.0 (experimental) - 2026-11-09
- Remove the duplicate Close button from modal Help, Keyboard Shortcuts fallback and System Information dialogs. Keep the native Adwaita titlebar close button and Esc.
- Give the standalone windowed/fullscreen GTK renderer the same Wayland application ID as the dashboard, using Gio.ApplicationFlags.NON_UNIQUE so the renderer never steals the control panel D-Bus name. This should allow Preview to associate with ASCII Saver's desktop entry; actual GNOME/KDE grouping still needs validation.
- Fix palettes appearing stuck on their first color. Multi-color palettes cycle automatically by default, once per successfully completed animation. Legacy config files containing the old implicit `cycle_palette: false` migrate to cycling. New `palette_mode: static` is written when users explicitly disable cycling in V106 and is honored on reload. Preserve smooth interpolation, ping-pong and per-display palettes.
- Rebuild cramped controls in Preferences as proper Adw.PreferencesRow custom layouts which move the selector below the label below 620sp, including advanced numeric controls. Remove the Save/Discard overlay covering the first rows and use a stable bottom action tray instead. These are source-tested UI changes, not yet visually validated on real GTK/Wayland.
- Add 11 new headless regression tests, update superseded overlay/duplicate-close contracts, and retain old release notes.
- See [RELEASE-V106.md](docs/releases/RELEASE-V106.md).

## 0.105.0 (experimental) - 2026-11-08
- Repair the Preferences startup NameError caused by unsaved-change banner
  widgets referenced outside their method scope. Route Preferences requests
  directly without first presenting the dashboard.
- Introduce unified `ascii-saver` command dispatch for Dashboard,
  Preferences, Playlist Editor, fullscreen/preview controls and diagnostics;
  retain old launcher aliases and renderer flags. Update desktop entry and
  ensure `ascii-saverctl start` explicitly runs the renderer.
- Present Help and System Information in modal transient Adwaita windows
  with an explicit Close button and Escape handling.
- Add 13 new headless regression tests, update superseded source contracts,
  and preserve the distinction between offline tests and live GTK validation.
- See [RELEASE-V105.md](docs/releases/RELEASE-V105.md).

## 0.104.0 (experimental) - 2026-11-08
- Synchronize fullscreen monitor launches with one GTK main-loop callback
  after the last per-monitor final-frame hold, rather than independent
  per-monitor restart timers. Shared playlist advancement and deterministic
  palette round progression remain unchanged.
- Batch initial multi-monitor launches and new hotplugged monitor launches.
  Tag each pending callback with its shared round and discard obsolete
  callbacks after hotplug, shutdown or advance. Windowed Preview is unchanged.
- Add simulated monitor/round/hotplug regression tests and update legacy fake
  window fixtures. Real GTK/Wayland timing must still be measured on devices.
- See [RELEASE-V104.md](docs/releases/RELEASE-V104.md).

## 0.103.0 (experimental) - 2026-11-08
- Add an optional **Reverse palette at the ends** appearance switch. With three or more colors, palette progression now supports first → middle → last → middle → first, rather than jumping from last to first. Existing cyclic behavior remains the default for saved and legacy configurations.
- Interpolate between effects in either direction with the existing Effects per color transition setting. Preserve deterministic shared-round synchronization across displays, per-monitor palette overrides and preview's independent progression.
- Validate and persist the new boolean setting, track it in unsaved-change detection, and add headless regression tests.
- See [RELEASE-V103.md](docs/releases/RELEASE-V103.md).

## 0.102.0 (experimental) - 2026-11-08
- Restore KDE/GNOME idle watcher **renderer ownership parity**. KDE's
  automatic idle launch now checks the live, exact-script renderer PID file
  before attempting to spawn, so an already-running manual Preview/Start is
  left untouched. Its idle request remains deferred and may run only after
  the existing renderer exits, provided no user activity, lock or inhibitor
  invalidates the wait. GNOME uses the same identity check for its existing
  duplicate-renderer guard.
- Add a common, dependency-free Linux C/C++ process identity helper validating
  bounded, regular, non-symlink PID files, same-user `/proc` process ownership,
  exact `argv[1]` renderer script and exact executable identity for native
  watcher processes. No guessing from name substrings or unverified PIDs.
- Make the GNOME watcher PID claim resilient to reused/stale PIDs using a
  held nonblocking `flock()` on the runtime PID file, while still refusing to
  replace a genuinely running legacy watcher. Release only the originally
  claimed inode and only if it still contains our own PID.
- Add native C and C++ compiled probes with live child processes, invalid
  and symlinked PID files, wrong-path/argv tests, plus source-level watcher
  integration contracts. Actual Qt/KIdleTime and GNOME/GIO builds and desktop
  idle behavior remain unverified until suitable dependencies/devices exist.
- Full details: [RELEASE-V102.md](docs/releases/RELEASE-V102.md).


## 0.101.0 (experimental) - 2026-11-08
- Resume work on the **core playback lifecycle**, rather than only Artwork
  Studio. Start Now, Preview and Stop now distinguish fullscreen from windowed
  mode, reject conflicting launch requests without changing the active session
  and treat same-mode launches as harmless repeats.
- Wait for the identity-verified renderer to exit after Stop (bounded 2.5 s)
  before reporting success; timed-out stops fail rather than claiming the
  application has closed. No additional force-kill behavior is introduced.
- Show **Preview running** vs **Fullscreen running** in the dashboard and add
  playback mode to `ascii-saverctl status`; keep watcher and automatic
  activation status independent.
- Serialize dashboard playback actions so the periodic UI refresh cannot
  re-enable controls during a command. Split execution into a GTK-free
  `dashboard_playback.py`, bound subprocess time to 10 s and preserve error
  messages for failed launches/stops. Add new lifecycle and UI contracts.
- Full details: [RELEASE-V101.md](docs/releases/RELEASE-V101.md).

## 0.100.0 (experimental) - 2026-11-08
- Add a compact **Work area** popover in Draw on Canvas to expand its visual
  grid to 48-200 columns and 18-100 rows, with Apply size and Fit to artwork.
  Existing text is not resized or cropped; unpainted cells are never stored.
  Brush and eraser can now reach distant empty cells without seeding the
  artwork with spaces. Save/Undo/Redo behavior remains unchanged.
- Limit Canvas grid, monospaced text layout and stroke-preview rendering to
  the visible scroll viewport plus one guard cell. This avoids laying out
  off-screen rows of large ASCII artwork on every redraw while preserving
  V98/V99 logical pointer coordinates and zoom.
- Add GTK-free expanded-area, safety, viewport-culling and UI wiring tests.
  Live GNOME/KDE scrolling and work-area popover verification is still open;
  the Rust renderer has not been rebuilt.
- Full details: [RELEASE-V100.md](docs/releases/RELEASE-V100.md).

## 0.99.0 (experimental) - 2026-11-08
- Let Canvas users move a visible cell cursor using arrow keys, apply their
  current brush glyph via Space, and erase with Delete/Backspace. One edit is
  one native Gtk.TextBuffer Undo/Redo action; the active cell follows the
  scrollable viewport and its 1-based coordinates appear in the existing
  hint line. Modifier shortcuts and text-only mode remain unchanged.
- Fix Canvas commits replacing the whole text buffer unnecessarily. Commit
  only the changed span and defer Canvas refresh until the grouped buffer
  update completes, avoiding transient empty states and resetting the active
  drawing cell. No implicit Save or on-disk file format change.
- Add GTK-free keyboard, bounds, scrolling and simulated intermediate-buffer
  regression tests. Live GNOME/KDE keyboard/fractional-scale testing remains
  open. No Rust renderer rebuild is claimed.
- Full details: [RELEASE-V99.md](docs/releases/RELEASE-V99.md).


## 0.98.0 (experimental) - 2026-11-08
- Improve the V97 **Draw on Canvas** workflow with bounded zoom choices (75%, 100%, 125%, 150%, 200%), a switchable non-destructive cell grid, and a secondary toolbar that wraps complete tool groups on narrow windows. Only the view changes; artwork text, dimensions, Save, and files are not modified by zoom or grid changes.
- Use Pango-measured logical character-cell geometry consistently for painting and drawing. Keep the top-left visible character approximately anchored on zoom, clamp scroll adjustments after GTK resizes the canvas, and reject stale scheduled scroll updates when zoom changes rapidly. ScrolledWindow remains responsible for navigation around large artwork.
- Add focusable Canvas keyboard Undo/Redo (`Ctrl+Z`, `Ctrl+Shift+Z`, `Ctrl+Y`), restoring focus to Canvas after the history action rather than to the hidden Text view. Cancel any unfinished stroke on zoom or switching back to Text mode.
- Add GTK-free geometry, scrolling, keyboard-controller and focus behavior tests. Existing renderer and artwork persistence formats are unchanged. Live fractional-scale GNOME/KDE Wayland pointer accuracy, zoom layout and scroll restoration still need physical validation; no rebuilt Rust renderer is claimed.
- Full details: [RELEASE-V98.md](docs/releases/RELEASE-V98.md).


## 0.97.0 (experimental) - 2026-11-08
- Add **Draw on Canvas** to the existing ASCII Artwork Editor, with a scrollable monospaced cell grid, pointer hover indicator, instant in-progress brush preview, continuous left-mouse dragging, one-character ink and Erase toggle. The normal Text mode remains available for keyboard editing and non-ASCII art.
- Interpolate rapid cursor motion across skipped cells, preserve original artwork line endings and untouched whitespace, allow filling empty rows, and avoid extending text when erasing blank grid cells. Limit canvas mode to 200 columns, 100 rows and printable 7-bit ASCII; unsupported material remains safely accessible in Text mode.
- Commit each mouse stroke to the same GtkTextBuffer in a single grouped Undo operation, without writing a file, changing the artwork's source photo or bypassing the existing Save/Discard rules. Keep native Undo/Redo and current tool palette.
- Add GTK-free interpolation, geometry, Unicode/size protection, no-overwrite and simulated native-buffer tests. Installer and docs updated. Full GTK mouse/input/focus/scroll and GNOME/KDE testing still required; no Rust renderer rebuild claimed.
- Full details: [RELEASE-V97.md](docs/releases/RELEASE-V97.md).


## 0.96.0 (experimental) - 2026-11-08
- Add a collapsed-in-popover **Retouch** tool in the existing artwork editor.
  Select a printable ASCII ink from a palette or enter one character, Paint
  at the caret (overwrite or append before the newline) and Erase at the caret
  (replace with a blank, without growing the canvas). Invalid ink and selected
  text cannot be silently repainted.
- Add **Mirror Selection** for horizontal retouch, including direction-aware
  slashes and brackets with rectangular spacing, and **Flip Selection** to
  reverse line order. Preserve trailing newline and reject oversized/invalid
  selected regions.
- Enable bounded native Gtk.TextBuffer Undo/Redo with grouped retouch edits;
  Save, dirty-buffer discard confirmation and separate photo projects remain
  unchanged. No automatic disk writes, mouse painting or layers are claimed.
- Add GTK-free cell/selection/edit safety tests, native GTK integration source
  checks, installer inclusion of `artwork_retouch.py` and updated milestone
  status. Full GNOME/KDE keyboard, focus and responsive UI testing pending.
- Full details: [RELEASE-V96.md](docs/releases/RELEASE-V96.md).

## 0.95.0 (experimental) - 2026-11-08
- **Online discovery performance and creative browsing:** Browse Online now renders at most 48 remote ASCII entries on a filter/sort change, with an explicit **Show More Artwork** button that appends the next batch without resetting selection and scroll position. Search no longer allocates every art card on each keystroke.
- Add **Sort**: Repository order, Title A–Z, Smallest first, Largest first, and seeded Shuffle. **Surprise Me** makes a fresh random ordering from the already loaded matching collection; the same shuffle remains stable when paging and never downloads extra data.
- Harden online refresh UX: prevent parallel refreshes, disable import during loading, keep existing in-memory artworks visible if refresh fails, preserve a selected tag on successful refresh when it still exists, and report shown/matched/total results accurately. No automatic importing, rewriting, or background polling.
- Documented ascii-bin feed confirmed reachable through public web inspection on 2026-11-08, but direct online fetch and GTK/KDE/GNOME interactions could not be executed in the working container. Added deterministic headless sorting/shuffle/page tests and source-level GTK contracts.
- Full details: [RELEASE-V95.md](docs/releases/RELEASE-V95.md).

## 0.94.0 (experimental) - 2026-11-08
- Add a **Custom** character-density ramp to Photo to ASCII: enter 2–63 unique printable 7-bit ASCII symbols from darkest to lightest. A final whitespace cell is implicit, so pure-white and center-fit padding render as blank cells. Choosing Custom reveals the existing collapsed Advanced section automatically.
- The custom ramp drives the actual renderer-safe monochrome text output and the same debounced side-by-side/stacked live preview. No ANSI escapes, arbitrary Unicode, multi-column characters or remote code enter the `.txt` asset.
- Restore the exact custom ramp in saved photo projects and conversion presets, and load earlier V89–V93 recipes lacking it with the same neutral default. Existing built-in ramps and results are unchanged.
- On invalid input, show inline error status, disable Use/Save, and clear the previous preview instead of leaving a stale artwork visible or spamming toast notifications. Switching back to a built-in ramp restores normal rendering even if the unfinished custom text remains on screen.
- Add V94 headless tests for pixel density mapping, validation, preset/project compatibility, safe preview failure and GTK UI wiring. Real live GTK/VTE/GNOME/KDE testing remains outstanding.
- Full details: [RELEASE-V94.md](docs/releases/RELEASE-V94.md).

## 0.93.0 (experimental) - 2026-11-08
- Extend the Photo to ASCII **Advanced image tools** with optional posterization (2–8 luminance bands or Off) and a choice of white, gray or black backdrop when compositing translucent RGBA photos. Keep basic mode uncluttered and the existing live side-by-side/stacked comparison responsive to changes.
- Make transparency controls inactive for photos without an alpha channel. Defaults are unchanged (no posterization, white background), preserving V92 output unless the user opts in. Center-fit padding remains blank regardless of the matte.
- Retain and restore both options in saved photo projects and user conversion presets; V89–V92 projects and V91–V92 personal presets that lack the new fields still load with original defaults. Validate invalid or unknown data rather than silently discarding it. Adjust the built-in Graphic Ink and 8-Bit Arcade looks to use distinct, intentional tone-limited effects.
- Add headless conversion, alpha, legacy-schema migration and GUI wiring regressions; full GTK/Wayland visuals and remote network validation remain unverified.
- Full details: [RELEASE-V93.md](docs/releases/RELEASE-V93.md).


## 0.92.0 (experimental) - 2026-11-08
- Add **Artwork Details** to the local My Artwork library: creator, description, stated license and HTTPS source URL alongside existing tags. Keep version-1 metadata readable and use validated atomic version-2 sidecar writes; never rewrite renderer `.txt` files or erase attribution when updating tags.
- Add opt-in **Browse Online** with an initial source, the publicly available [ascii-bin](https://github.com/amwhoi/ascii-bin) collection. Its documented plain-text feed supports text previews, searchable descriptions/tags, shape/tag filters and explicit Import a Copy. Responsive list/preview layout; network download runs outside GTK's main thread.
- Enforce strict remote payload and artwork limits, control-character sanitation, safe private cached fallback for offline use, exclusive local file creation, and rollback on metadata failure. Imports record source and an explicit warning: the repository claims CC0, but does not verify rights of all original contributors. No automatic commercial-use claims or online publishing.
- Add headless provider/metadata/migration/rollback/caching tests and GTK UI source contracts; package new modules. **Live HTTPS, GTK and GNOME/KDE Wayland testing not performed** in this environment.
- Full details: [RELEASE-V92.md](docs/releases/RELEASE-V92.md).

## 0.91.0 (experimental) - 2026-11-08
- Add **Creative Looks** to Photo to ASCII: six clearly differentiated, offline conversion recipes (Classic Terminal, Film Noir, Soft Horizon, Graphic Ink, 8-Bit Arcade and Architectural Detail). Selecting and applying one updates the same live preview and editing controls, without saving over an existing asset or changing the original photo.
- Add **My conversion presets** as a collapsed advanced area. Users can explicitly save current basic/advanced conversion settings under a meaningful name, reapply personal presets or remove them with confirmation; built-in presets cannot be deleted. Reject duplicate visible names, invalid files and unsafe paths.
- Store personal presets in a versioned, bounded, validated `photo-presets/*.json` directory. Exclusive-create + rollback protects from partial writes and overwrites. Malformed optional presets are skipped without breaking the six built-in styles. Saved photo-project recipe format remains compatible with V89/V90.
- Add headless persistence/security/round-trip tests, GTK UI wiring tests and installer payload. **Actual GTK/Wayland UI layout, keyboard operation and KWin grouping remain unverified.**
- Full details: [RELEASE-V91.md](docs/releases/RELEASE-V91.md).

- Artwork Studio remains in progress: richer image tools, additional library metadata, and vetted online artwork browsing are planned. GTK/KDE/GNOME live verification is outstanding.

## 0.90.0 (experimental) - 2026-11-08
- Add **My Artwork**, a responsive, offline local gallery directly from the native Artwork Editor. Real bounded text previews appear alongside artwork names, dimensions and orientation; Search matches filenames and user tags, with source (plain text/photo project) and shape filters plus one-click Clear Filters.
- Open a chosen asset in its own existing Artwork Editor, preserving the original editor's unsaved buffer and reopening the linked photo recipe when available. Multiple attempts to open the same asset while the gallery remains open reuse that window.
- Add explicit Edit Tags: up to twelve validated user labels stored atomically in private `artwork-meta/*.json` sidecars, never by rewriting the `.txt` artwork. Broken metadata does not hide valid art. Reject symlinked libraries, oversized/invalid text, unexpected metadata and unsafe paths.
- Allow **Save a Copy** of any of the eight original creative templates to a new collision-safe user artwork from the gallery. No implicit overwrite or online dependency.
- Add GTK-free indexing/filtering/metadata/security tests and UI source contracts. All GTK rendering, sizing and keyboard accessibility remain to be tested on actual GNOME/KDE systems.
- Full details: [RELEASE-V90.md](docs/releases/RELEASE-V90.md).

## 0.89.0 (experimental) - 2026-11-08
- Save as New Artwork in Photo to ASCII now stores a self-contained, versioned conversion project alongside the renderer-compatible `.txt`: an exact copy of the original photo, SHA-256 checksums, and the full set of basic/advanced conversion settings. Plain text assets and existing saved artwork remain compatible.
- Artwork Editor offers **Reopen Photo** for artwork with a saved project. The photo and all conversion controls are restored for live preview; exporting produces a new, collision-safe artwork instead of overwriting either the old `.txt` or original source image. When the `.txt` was manually changed, the editor explains that those text edits are separate from the photo recipe.
- Reject tampered project metadata, source hash mismatches, path traversal, symlinked storage folders and oversized files. Failed writes roll back the newly created project and artwork; stored project metadata never contains arbitrary external source paths or executable instructions.
- Update installer, UI, documentation and headless persistence/rollback/reopen regression tests. **GTK/Wayland UI operation, source import and real desktop integration are not verified.**
- Full details: [RELEASE-V89.md](docs/releases/RELEASE-V89.md).

## 0.88.0 (experimental) - 2026-11-08
- Add progressive Advanced image tools in the Photo to ASCII editor: gamma correction (0.5–2.5), local edge definition (0–100) and optional Floyd-Steinberg dithering with a one-action reset, collapsed by default.
- Separate tone sampling, optional edge contrast and glyph quantization; respect letterbox padding, bounds and selected character ramp. Neutral defaults reproduce the V87 conversion behavior.
- The existing live side-by-side/stacked preview is updated by the same debounced controls, while explicit Save as New and Use in Editor continue to protect the original file and unsaved text.
- Add headless behavioral tests for gamma, dithering, edges, padding and GUI contracts; update TASKS, ROADMAP, backlog and release notes. Live GTK/Wayland validation and full photo recipe persistence are still outstanding.
- Full details: [RELEASE-V88.md](docs/releases/RELEASE-V88.md).

## 0.87.0 (experimental) - 2026-11-08
- Add a built-in Photo to ASCII window from Edit Artwork, with local PNG/JPEG/WebP/BMP import, bounded RGB/RGBA conversion, alpha-on-white compositing, terminal-cell aspect correction, center crop or full-image fit.
- Live original/ASCII comparison side by side, stacking vertically under a libadwaita breakpoint; edit width, height, brightness, contrast, inversion and three density mappings with debounced previews.
- Export through explicit Save as New Artwork into the existing local `.txt` library using exclusive creation and duplicate-safe names, or Use in Editor with unsaved-text confirmation. No implicit overwrites of source photos or existing artwork.
- Headless conversion/export safety tests, installer module updates, TASKS/ROADMAP/BACKLOG updates. GTK/Wayland visual and live file-chooser tests remain unverified.
- Full details: [RELEASE-V87.md](docs/releases/RELEASE-V87.md).

## 0.86.0 (experimental) - 2026-11-08
- Start the approved Artwork Studio milestone with eight original creative ASCII templates, an offline searchable style chooser, responsive side-by-side/stacked sample preview, and safe insertion into the existing built-in text editor.
- Keep current Save/Discard semantics: applying a template modifies only the buffer, asks before replacing unsaved edits, and never writes the artwork to disk without explicit Save.
- Consolidate active UX goals and future milestones into `ROADMAP.md`, link from `TASKS.md`, `MASTER-BACKLOG.md` and README. Archive the original V54 UX roadmap verbatim instead of losing history; preserve specialized renderer backlogs and release records as evidence.
- Add headless tests for template quality, selection/dirty-state safeguards, responsive preview contracts, packaging and document links. GTK/GNOME/KDE Wayland validation remains open.
- Full details: [RELEASE-V86.md](docs/releases/RELEASE-V86.md).

## 0.85.0 (experimental) - 2026-11-08
- Responsive Effect Library: replace fixed three-column grid with a 1–3-column FlowBox while keeping selection, preview and scroll region intact.
- Stack search/filter and preview actions on narrow library windows, and stack Playlist Editor filters when its navigation collapses.
- Add a clear empty-search state and one-action filter reset to both galleries. These UI-only filters preserve saved and unsaved effect selections.
- Add headless regression tests for filter/reset behavior and UI layout contracts. GNOME/KDE Wayland GUI behavior is not verified.
- Full details: [RELEASE-V85.md](docs/releases/RELEASE-V85.md).

## 0.84.0 (experimental) - 2026-11-07
- E02/B213 source correction: make Playlist Editor a reusable application-owned window instead of launching a second, differently identified Wayland application process.
- Make Effect Library an independent application window rather than a transient Preferences dialog, so KDE Task Manager is allowed to show it and group it under ASCII Saver.
- Reuse one playlist editor, release its live PTY preview and animated thumbnails at close, and reload only saved playlists without discarding unrelated unsaved Preferences changes.
- Add GTK-free lifecycle and identity regression tests. KDE Wayland taskbar behavior remains unverified.
- Full details: [RELEASE-V84.md](docs/releases/RELEASE-V84.md).

## 0.83.0 (experimental) - 2026-11-07
- Restore a complete issue index in `MASTER-BACKLOG.md`, cross-linked from `TASKS.md` and the README; retain historical backlogs and distinguish source implementation, runtime verification and deferred ideas.
- Fix narrow dashboard and Preferences watcher/renderer labels (A05): bound long text to a single line and keep the full value readable/selectable through tooltips, without changing process states or creating new background services.
- Add headless regressions for status presentation and release tracking. Full GTK/KDE/GNOME visual confirmation is still pending.
- Full details: [RELEASE-V83.md](docs/releases/RELEASE-V83.md).

## 0.82.0 (experimental) - 2026-11-07
- Show visible qualitative duration and intensity labels on every Effect Library and Playlist Editor card (D05), consistent with existing filters.
- Distinguish automatic activation from native watcher process status on the main dashboard; Configure opens Preferences (B212).
- Create TASKS.md as the current checked issue tracker; reconcile stale hot-plug checkbox in historical roadmap.
- Add headless regression tests and install new shared card metadata module. GTK/GNOME/KDE runtime validation remains pending.
- Full details: [RELEASE-V82.md](docs/releases/RELEASE-V82.md).

- Documentation-only update: reconstructed dates for all surviving release entries (V19–V81), retaining estimated-date labels where evidence is incomplete.

## 0.81.0 (experimental) - 2026-11-07
- Removed the duplicated visible Effect Library Play selector from Preferences; the library now owns the visible choice (B214).
- Kept saved `effect_preview_mode`, synchronization with the internal state control, partial Save/Discard and existing preview behavior unchanged.
- Reordered and backfilled documented version history. Added GTK-free tests of preview-control ownership and release tracking.
- Full details: [RELEASE-V81.md](docs/releases/RELEASE-V81.md).

## 0.80.0 (experimental) - 2026-11-07
- Refresh per-monitor FPS, palette and artwork settings when displays are attached or removed while Preferences is open.
- Preserve in-progress controls across disconnect/reconnect, and avoid false unsaved-change banners for newly connected monitors.
- Merge saved per-monitor mappings instead of erasing settings for currently disconnected screens.
- Added headless regression tests and installer payload for monitor_config.py. Full GNOME/KDE hot-plug validation pending.

## 0.79.0 (experimental) - 2026-11-07
- Fixed GTK header width retention when switching from five-tab navigation to compact dropdown; moved the compact breakpoint to 600sp.
- Kept Save/Discard accessible on narrow windows and allowed per-monitor artwork/color controls to wrap instead of clipping.
- Reduced fixed timing-slider widths and shortened Preview selector labels while preserving existing settings values.
- Added GTK-free B01/B02 regression tests; live GNOME/KDE verification remains pending.

## 0.78.0 (experimental) - 2026-11-07
- Moved `Run Diagnostics` to a separate read-only, grouped Adwaita window with named PASS/FAIL checks, rerun, clear, and copy actions.
- Kept diagnostic scanning off the GTK main thread and ignored late results from cleared or closed windows.
- Added explicit confirmation before discarding unsaved ASCII artwork edits.
- Editor completion messages now reflect an actual disk save or close without changes, never merely opening an editor.
- Added headless diagnostic and artwork workflow regression tests.

## 0.77.0 (experimental) - 2026-11-07

- Center the terminal-effect canvas in independent and pinned single-effect previews using the existing Rust `--anchor-canvas c` implementation. The canvas is recomputed from terminal dimensions after resize; no animation changes.
- Put Replay directly in the independent preview header and remove its duplicate Close button and explanatory copy. The normal window close button remains.
- Increase pinned Effect Library preview height to 240–280 logical pixels and default gallery window to 1000 × 860 while preserving a 320-pixel minimum scrollable card viewport. Remove redundant Preview behavior Help card.
- Let users toggle an effect by clicking its animated Effect Library thumbnail; Play remains separate.
- Add GTK-free regression tests. GTK/VTE and live Wayland sizing require later real-device verification.

## 0.76.0 (experimental) - 2026-11-07

- Improve measured performance readability: Adwaita groups for per-display and shared GTK/VTE data, vertical scrolling and copyable descriptive rows.
- Show monitor legends, independent scale/ticks per CPU, RSS, GPU engine and output FPS chart; display FPS as discrete completion events.
- Explain median and number of completed runs in measured durations; keep preview/display selector.
- Use a pure Python performance summary model with invalid-value and process-accounting tests.
- Full Wayland GTK/VTE visual verification remains pending.

## 0.75.0 (experimental) - 2026-11-07
- Redesigned Playlist Editor around a large, expanding animated effect gallery,
  while retaining a separate list for playlist ordering.
- Collapsed playlist details and automatic/measurement generation into a
  bounded options panel, freeing space for effect previews.
- Added search, active playlist and selection counts, and an empty-filter state;
  filters cannot mutate selected effects.
- Unified selection borders and thumbnail hover/focus styling; kept independent
  Preview and explicit Save/Discard behavior.
- Added GTK-free gallery-model and layout regression tests.

## 0.74.0 (experimental) - 2026-11-07
- Context-local Save/Discard overlays in Effect Library and Playlist Editor.
- Library partial saves update only effect inclusion and preview mode, without
  marking unrelated unsaved Preferences values as saved.
- Playlist Editor Discard restores its saved playlist baseline, and changes in
  both editor windows are tracked across all relevant controls.
- Returning from Playlist Editor updates only playlist JSON, preserving all
  other unsaved Preferences changes and warning about raw JSON conflicts.
- Added prioritized, evidence-based backlog and GTK-free regression tests.

## 0.73.0 (experimental) - 2026-11-07
- Keep the final frame intact in both Effect Library live preview modes. The inline
  preview previously omitted `--no-eol` and `--no-restore-cursor`; the separate
  preview omitted `--no-eol`. Both now use the same Rust output-completion flags
  as fullscreen and persistent preview.
- Hide the inline VTE text insertion cursor before its first frame and again
  after its child exits. Cursor suppression does not affect the mouse pointer
  or cause live previews to dismiss on user input.
- Protect fullscreen animation completion from permissions errors while deleting
  temporary statistics reports. Failure to clean a report now logs a warning
  instead of aborting the callback and leaving synchronized monitors waiting.
- Add GTK-free regressions for CLI flags, callback cursor behavior and failure
  cleanup. GNOME/KDE visual validation and a Rust build remain deferred.

## 0.72.0 (experimental) - 2026-11-07
- Recolored Effect Library and Playlist Editor sample thumbnails with the first global palette color and selected background, including unsaved edits in an open Effect Library.
- Added 886 low-resolution coverage masks to the 37 existing sample-animation archives. Recoloring uses a fast lookup without decoding full GIFs or invoking the Rust renderer.
- Original RGBA samples remain available for backward compatibility. Old packs are still supported through a slower fallback.
- Updated packaging, independent release checks and regression tests. GTK/Wayland visual testing is still pending.

## 0.71.0 (experimental) - 2026-11-07

- Ensure the chosen ASCII Saver palette controls all effect output, including effects with embedded ANSI/truecolor gradients: launch the bundled Rust `ttfx` with `--no-color` in fullscreen, persistent preview, and library live preview.
- Preserve terminal background, symbol animation and effect geometry while suppressing effect-specific foreground/background escape codes; per-monitor and between-effect colors remain selected by the V70 palette engine.
- Apply the currently selected (even unsaved) preferences colors to both library live preview modes, instead of showing the terminal's own hardcoded default.
- Update preferences guidance and add 7 regression tests, including GTK-free VTE palette and live-child option wiring checks.

## 0.70.0 (experimental) - 2026-11-07

- Advance fullscreen palette colors by the global synchronized playback round,
  not by individual monitor child-spawn attempts. Failed launches and retries
  now reuse the same color until a genuinely new round starts.
- Advance the persistent preview's palette only after successful effect exit;
  preview progression remains independent of all fullscreen displays.
- Validate and normalize user-defined and per-monitor color palettes in a
  standalone palette engine. Whitespace-padded hex values no longer break
  RGB interpolation, and malformed overrides fall back to the shared palette.
- Use the same color step on all monitors while still honoring independent
  monitor palettes. Preview always uses the shared palette.
- Stage the new palette module in the installer, with headless tests exercising
  the renderer's real VTE color-setting method.

## 0.69.0 (experimental) - 2026-11-07

- Honor auto-fit in shared monitor mode using the smallest common font needed
  to fit the artwork on all displays, while preserving independent per-display
  font sizes for independent monitor mode.
- Reset VTE to the configured font for every effect and preserve an explicit
  auto-fit Off option in both modes.
- Move auto-fit into the always-visible Displays options and correct estimates
  for per-display artwork.
- Isolate mutable configuration defaults between loads.
- Add headless runtime font-fitting tests and font-plan regression coverage.

## 0.68.0 (experimental) - 2026-11-07

- Isolate windowed preview playlist scheduling from the fullscreen playback
  cursor. Preview advances can no longer consume fullscreen playlist entries.
- Use a per-monitor shuffle bag for unordered fullscreen effects, without
  repeats until all enabled effects have been played.
- Avoid a repeated effect at shuffle-playlist cycle boundaries when possible.
- Add headless regression coverage for playlist separation and the existing
  multi-monitor hold-and-advance barrier.

## 0.67.0 (experimental) - 2026-11-07

- Register the renderer's previously missing `app.quit` action so the
  fullscreen `Escape` accelerator has an actual handler.
- Keep the accelerator disabled in persistent windowed previews, where
  keyboard/mouse activity must not terminate the session.
- Give the primary GTK layer-shell surface exclusive keyboard interactivity
  *before* its first `present()`. Other monitors remain non-interactive for
  keyboard input, and the owner is refreshed after hotplug.
- Add GTK-free regression tests for the first-map keyboard assignment and
  explicit quit action. Runtime GTK/VTE and compositor focus remain to be
  verified on the target desktop.

## 0.66.0 (experimental) - 2026-11-07

- Fullscreen GTK4/VTE screensaver uses an input-capable, transparent pointer
  overlay to hide GNOME's text-selection I-beam without a shell extension.
- Preview remains unmodified; motion/key dismiss continue via capture phase.
- V65 GNOME cursor bridge is now opt-in using `ASCII_SAVER_GNOME_CURSOR_BRIDGE=1`;
  it no longer activates automatically if an old extension is installed.
- Added offline regressions and GNOME live validation checklist.

## 0.65.0 (experimental) - 2026-11-03
- GNOME fullscreen renderer publishes a session D-Bus lease *only while mapped*.
- Extension watches lease ownership, uses Mutter's cursor visibility API and restores the pointer on name disappearance, screen lock or disable.
- Windowed preview and KDE never publish the lease.
- Full details: [RELEASE-V65.md](docs/releases/RELEASE-V65.md).

## 0.64.0 (experimental) - 2026-11-03

- Optional, reversible GNOME Dash to Dock fullscreen compatibility profile; read-only status and explicit apply/restore commands.
- Documentation of GNOME Shell compositor limitations and post-unlock dock behavior.
- No changes to cursor handling or fullscreen renderer implementation.

## 0.63.0 (experimental) - 2026-11-03 (estimated)
- GNOME HIG primary-menu button in the dashboard, with Preferences, Keyboard Shortcuts, Help, About, and Quit; System Information is kept separately.
- Standard keyboard shortcuts (Ctrl+, / Ctrl+? / F1 / F10 / Ctrl+W / Ctrl+Q).
- Uses Adw.AboutDialog and Adw.ShortcutsDialog where available; older libadwaita uses native-window fallbacks.
- Full details: [RELEASE-V63.md](docs/releases/RELEASE-V63.md).

## 0.62.0 (experimental) - 2026-11-02
- The GTK4 fullscreen cursor mitigation in V61 did not work in the Fedora GNOME/Mutter test. V62 uses GTK4's documented named `none` cursor, attaches realize/map handlers **before** presenting the fullscreen window, and applies the cursor to the root GTK widget, VTE child, GDK surface, and default pointer device. It reasserts the cursor on pointer-enter without polling or cursor warping. The normal windowed preview keeps its ordinary pointer.
- Full details: [RELEASE-V62.md](docs/releases/RELEASE-V62.md).

## 0.61.0 (experimental) - 2026-11-02 (estimated)

- Dashboard reacts to the live GDK monitor list, changing its start action's title and subtitle between singular and plural wording without a periodic refresh.
- Displays Preferences immediately updates connected monitor count. Per-monitor editing controls are still built on window creation; dynamic control rows remain in the backlog.
- Reapply the transparent pointer cursor when GTK's fullscreen Wayland window is mapped, including to the surface itself.
- Document Dash to Dock's overlap after lock/unlock as a GNOME Shell stacking issue. No guarantee is made that regular fullscreen can overlay a Shell extension, and we do not modify or disable extensions automatically.

## 0.60.0 (experimental) - 2026-11-02
- **Edit Artwork (Preferences / General):** open the existing in-app `Adw.Window` text editor directly, instead of running `ctl.py edit` in a subprocess with captured stdout. Captured terminal editors could output ANSI escape codes into the page rather than displaying a graphical editor.
- **Clean application identity:** installer and uninstaller operate only on `ascii-saver`. The installer does not copy, move, stop or remove the legacy `kde-ascii-saver` files, configuration, service or cache. This also means updating from an old KDE-prefixed release will **not** automatically import its settings.
- **User data safety:** existing `~/.config/ascii-saver/` artwork and preferences remain untouched on upgrades; the old installation can be uninstalled independently.
- Full details: [RELEASE-V60.md](docs/releases/RELEASE-V60.md).

## 0.59.0 (experimental) - 2026-11-02 (estimated)
- Renamed application identity, launcher commands, desktop entry, service, config and cache directories from `kde-ascii-saver` to `ascii-saver`.
- Added backward-compatible migration of old preferences, artwork and Cargo cache without deleting source configuration.
- Fixed GNOME startup: queries `org.gnome.ScreenSaver` for lock state, not the freedesktop idle-inhibition service. KScreenLocker remains the KDE backend.
- Full details: [RELEASE-V59.md](docs/releases/RELEASE-V59.md).

## 0.58.0 (experimental) - 2026-11-01 (estimated)

- Automatically choose native KDE or GNOME idle watcher from desktop/session metadata.
- Detect and describe compositor/window manager and Wayland/X11 mode through `./install.sh --detect-session`.
- Recognize unsupported desktops (Sway, Hyprland, niri, COSMIC, etc.) and stop before unrelated Qt/KF6 dependency installation.
- Add installer and session-detection regression tests; preserve explicit backend override for troubleshooting.

## 0.57.0 (experimental) - 2026-11-01 (estimated)

- Fix GNOME installer failure from unconditional Qt6/KF6 CMake watcher build.
- Add native C/GIO GNOME watcher using Mutter IdleMonitor D-Bus, no resident
  Python interpreter for the watcher process.
- Add GNOME-specific dependency checks and systemd service activation.
- Preserve existing KDE watcher, Rust renderer, preferences and user files.

## 0.56.0 (experimental) - 2026-10-18
- Independent preview sequencing via `preview_sequence.py` with shuffle-bag rotation or ordered playlist advancement and configured hold.
- Native Adwaita artwork editor with atomic UTF-8 saves, used by per-monitor Edit actions.
- Instant dashboard status refresh on Preferences Save; short `Saved.` toast.
- Auto-fit control moved into independent-display options; guard stale shared-mode auto-fit configurations.
- Added corresponding pure-Python regression tests and packaged new modules.

## 0.55.0 (experimental) - 2026-10-18
- This version adds persistent Cargo release cache, a Preview/Close Preview dashboard button replacing Stop, fixes repeated playlist effects in windowed preview, shuffles shared effects across rounds when not ordered, reserves reset-button width (no slider jump), shortens the save toast to Saved, unifies watcher/renderer status models, and makes monitor artwork chooser/Edit/Reset controls clearer. A watcher-memory PSS diagnostic, renderer post-start failure log in `~/.cache/kde-ascii-saver/renderer.log`, and backlog are included.
- Full details: [RELEASE-V55.md](docs/releases/RELEASE-V55.md).

## 0.54.0 (experimental) - 2026-10-18
- **Factory reset buttons:** Every numeric setting in Preferences, including advanced animation timing, effect hold, idle delay, global/per-monitor FPS and palette steps, has a contextual restore-default icon. It appears only while the value differs from the immutable application default; resetting a previously saved custom value is tracked as an unsaved edit. Timing defaults: all multipliers and simulation hold = 1; FPS = 60. Sliders show their values above rather than on the right.
- **JSON editing:** Raw playlist JSON opens in a standalone text editor window with validation and explicit Apply to Preferences. Normal users should use the visual editor instead.
- **Adaptive categories and Save/Discard:** Removed duplicate titlebar Save action. The floating, non-layout-shifting banner is the single Save/Discard surface, with a solid Adwaita window background. At very narrow widths, header category dropdown replaces overflowing category tabs.
- Full details: [RELEASE-V54.md](docs/releases/RELEASE-V54.md).

## 0.53.0 (experimental) - 2026-10-17

- Modular libadwaita frontend and GTK-independent preferences validation. See [RELEASE-V53.md](docs/releases/RELEASE-V53.md) and [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 0.52.0 (experimental) - 2026-10-17
- Shared `adwaita_ui.py` with native preferences pages, groups and action rows.
- Replaced the legacy two-column `Gtk.Frame`/`Gtk.Grid` preference settings with `Adw.PreferencesPage`/`Adw.PreferencesGroup`/`Adw.ActionRow`.
- Preserved the five adaptive categories, and existing Save/Discard behavior.
- Full details: [RELEASE-V52.md](docs/releases/RELEASE-V52.md).

## 0.51.0 (experimental) - 2026-10-17
- Dedicated dashboard and adaptive libadwaita preferences with five navigation pages.
- Replay last library preview; close-time renderer cleanup.
- Installer libadwaita dependency and CLI preferences routing.

## 0.50.0 (experimental) - 2026-10-17

- Effect Library live previews now default to an independent, resizable window, reusable across effect selections and not dismissed by keyboard/pointer activity.
- Optional pinned live preview remains visible below the effect-card scroller while browsing.
- Mode selector available inside the library and Preferences, synced and stored in the user configuration.
- Explicitly terminate embedded preview subprocesses when the preview is stopped or the gallery is hidden.

## 0.49.0 (experimental) - 2026-10-16

- Rebuilt the Effect Library layout: its search/filter controls stay above an explicitly expanding, independently scrolling card viewport. The renderer preview is bounded below the viewport so it cannot collapse the library into a strip.
- The playlist editor now lets users toggle an effect by clicking its animation thumbnail. Each card has a separate Play icon that opens a nonmodal VTE preview of the actual artwork.
- Added a reusable one-effect preview window, with cancellation/renderer cleanup when closed. Installed alongside the playlist editor.
- Added source regression checks specifically for the scroll/preview layout, thumbnail selection, and preview launch, and retained viewport-limited asset decoding.

## 0.48.0 (experimental) - 2026-10-15

- Fixed preview spawn argument ordering; initial frame for thumbnails; consolidated Library and Playlist controls; raw playlist editor collapsed; floating unsaved banner.

## 0.47.0 (experimental) - 2026-10-15
- Pre-rendered the 37 bundled GIF effects offline into compact `.aspr` frame packs (ZIP containers holding compressed 224px RGBA frames, with up to 24 samples and durations). **Pillow is only needed when generating the packs; the installed application does not depend on Pillow.** The packs are included.
- GTK4 uses `Gdk.MemoryTexture` constructed directly from the small RGBA frames. No GTK/GdkPixbuf/Glycin GIF loader is used to present effect thumbnails.
- Both the Effect Library and Visual Playlist Editor activate thumbnails only while their cards intersect the scrolled window's actual viewport, plus a small scrolling margin. Offscreen readers stop timers and close files.
- Full details: [RELEASE-V47.md](docs/releases/RELEASE-V47.md).

## 0.46.0 (experimental) - 2026-10-14
- Animated gallery GIF playback now explicitly decodes and advances frames with GdkPixbufAnimation, Gtk.Picture and Gdk.Texture. Each preview starts only while mapped and stops updating while unmapped. All 37 supplied GIFs were verified as changing across frames.
- Effect Library moved into a separate, reusable window. The main preferences page no longer includes the 37-row gallery.
- Visual playlist editor gains animated effect previews, using the same mapped-only widget.
- Full details: [RELEASE-V46.md](docs/releases/RELEASE-V46.md).

## 0.45.0 (experimental) - 2026-10-14
- `ttfx-rust/src/engine/effect.rs`: remove the invalid outer `1..` in the simulation-hold paint loop. `repeat_count()` already returns `std::ops::Range<u32>`, and nesting it in another range triggers Rust `E0308` (expected integer, found `Range<u32>`).
- Add an offline regression guard that checks this specific source contract.
- Update the numeric CMake-compatible application version to `0.45.0`.
- Full details: [RELEASE-V45.md](docs/releases/RELEASE-V45.md).

## 0.44.0 (experimental) - 2026-10-14
- Fix CMake project VERSION by providing a strictly numeric VERSION (`0.44.0`).
- Invoke `scripts/dependency-hint.sh` with Bash so missing executable bits do not mask errors.
- Do not reinstall system dependencies on arbitrary CMake configuration failures after dependency checks have passed.
- Full details: [RELEASE-V44.md](docs/releases/RELEASE-V44.md).

## 0.43.0 (experimental) - 2026-10-14
- The GTK-dependent screen-lock lifecycle test now skips cleanly when PyGObject is absent, while still running on GTK-capable hosts.
- Added offline checks for the complete 37-effect GIF library: unique IDs, nonempty and valid GIF headers, installer staging and GUI lookup paths.
- `verify-build.sh` now runs pure-Python tests, release asset validation and installer tests before attempting Cargo.
- Full details: [RELEASE-V43.md](docs/releases/RELEASE-V43.md).

## 0.42.0 (experimental) - 2026-10-14
- Cards for all 37 effects, using GIF animations shipped with the ttfx source.
- Click the play button to preview the same effect with your own ASCII artwork.
- Three-column search/filter grid retains checkbox states.
- Full details: [RELEASE-V42.md](docs/releases/RELEASE-V42.md).

## 0.41.0 (experimental) - 2026-10-14
- The settings application now has an inline searchable library for all 37 effects, with suggested duration and intensity dropdowns, visible result count and existing one-at-a-time animated previews. Filtered-out effects retain their enabled state.
- Full details: [RELEASE-V41.md](docs/releases/RELEASE-V41.md).

## 0.40.0 (experimental) - 2026-10-14
- Fixed uneven output cadence in the reference Rust renderer when `--virtual-clock` and `--simulation-hold > 1` are used together with a positive FPS cap. The first output of each held group now uses the same pacing enforcement as the subsequent repeats.
- Full details: [RELEASE-V40.md](docs/releases/RELEASE-V40.md).

## 0.39.0 (experimental) - 2026-10-14
- Fixed an uncapped FPS busy-loop in the reference Rust renderer. With `--frame-rate 0`, `--simulation-hold` does not repaint an identical frame repeatedly. At positive FPS caps the configured repeat count is preserved. Added a Rust unit test.
- Full details: [RELEASE-V39.md](docs/releases/RELEASE-V39.md).

## 0.38.0 (experimental) - 2026-10-14
- A new `--simulation-hold N` (1..10) repeats each simulation frame N times at the output-frame cadence. This slows discrete-frame animations without skipping simulation steps, unlike modifying the FPS cap. N=1 is the original behavior. For N>1 the program uses the reference Rust engine rather than the optimized `fx` engine. The prior `--duration-factor` continues to affect output frame pacing, so set it to 1.0 when comparing modes.
- Full details: [RELEASE-V38.md](docs/releases/RELEASE-V38.md).

## 0.37.0 (experimental) - 2026-10-14
- Adds a **real executable smoke test** checking end-to-end CLI invocation, JSON output, effect identity, and frame counts in the instrumented Rust binary, across original and automatic engine dispatch.
- `./verify-build.sh` now runs that smoke test after the Cargo build, failing if the renderer contract is broken.
- Cleans unique `ttfx` report files on failed VTE launches and on application shutdown. Avoids accumulation of orphaned temporary files after errors.
- Full details: [RELEASE-V37.md](docs/releases/RELEASE-V37.md).

## 0.36.0 (experimental) - 2026-10-14
- Adds a fourth five-minute performance graph showing **measured ttfx active output FPS** per monitor, using completed `frame_stats` events.
- Adds a per-effect FPS summary and differentiates renderer output FPS from display-presented FPS and the configured FPS cap.
- Prevents frame statistics from being misinterpreted as CPU/RAM samples and excludes invalid measurements.
- Full details: [RELEASE-V36.md](docs/releases/RELEASE-V36.md).

## 0.35.0 (experimental) - 2026-10-14
- Fixes a confirmed schema-contract bug: Rust telemetry previously serialized Debug output (`Beams(BeamsConfig { ... })`) instead of the effect CLI key (`beams`). KDE rejected such reports when it checked the expected effect name.
- Full details: [RELEASE-V35.md](docs/releases/RELEASE-V35.md).

## 0.34.0 (experimental) - 2026-10-14
- The installer now builds the bundled Rust renderer with `cargo build --release --locked` automatically, or uses an explicitly specified `KDE_ASCII_SAVER_TTFX` binary after checking its CLI capabilities. It no longer silently selects a potentially incompatible system `ttfx`. Rust compilation occurs in a temporary transaction directory before installing the application files. A failed build stops installation without replacing the existing installed app. Requires Cargo and network access to any crates not cached locally.
- Full details: [RELEASE-V34.md](docs/releases/RELEASE-V34.md).

## 0.33.0 (experimental) - 2026-10-14
- Fixes `--virtual-clock --time-scale` so simulation time advances by `time_scale / frame_rate` each output frame.
- Preserves original virtual timing for `--parity-dump`, so parity test fixtures are unchanged.
- Adds two Rust regression tests, plus `./verify-build.sh` for actual Cargo tests and release build.
- Full details: [RELEASE-V33.md](docs/releases/RELEASE-V33.md).

## 0.32.0 (experimental) - 2026-10-14
- `ttfx --frame-rate 60 --time-scale 0.5 matrix` scales the internal elapsed clock of wall-clock effects while keeping the configured frame pacing. It is **not** universal duration scaling: effects based on discrete frame counts are unaffected. The separate `--duration-factor` option still scales delays and hence output FPS. Virtual-clock parity runs are unchanged.
- Full details: [RELEASE-V32.md](docs/releases/RELEASE-V32.md).

## 0.31.0 (experimental) - 2026-10-13
- Exposes Rust duration-factor in the GTK preferences, independent from the configured FPS multiplier control.
- Persists and validates duration_factor (0.5–10.0), default 1.0.
- Adds settings regression tests.
- Full details: [RELEASE-V31.md](docs/releases/RELEASE-V31.md).

## 0.29.0 (experimental) - 2026-10-13
- The ttfx Rust schema-2 reports are now accepted by the KDE application (the previous V28 reader only accepted schema 1). Active output FPS is recorded separately from lifetime-average output FPS. Schema-1 reports remain supported. Corrupt, failed, and effect-mismatched reports are rejected. The new parser is installed with the application.
- Full details: [RELEASE-V29.md](docs/releases/RELEASE-V29.md).

## 0.28.0 (experimental) - 2026-10-13
- `average_output_fps`: frames written divided by overall effect wall time, including setup.
- `active_output_fps`: intervals between the first and last successfully written frames, excluding setup and teardown. Null if fewer than two frames are produced.
- Full details: [RELEASE-V28.md](docs/releases/RELEASE-V28.md).

## 0.27.0 (experimental) - 2026-10-13
- This source archive contains the updated KDE application and a patched Rust ttfx source tree in `ttfx-rust/`.
- Full details: [RELEASE-V27.md](docs/releases/RELEASE-V27.md).

## 0.26.0 (experimental) - 2026-10-13
- This release adds a third, independently scaled five-minute performance graph for GPU engine busy time alongside CPU and RSS. It separates each monitor's process samples and does not manufacture 0% GPU utilization when DRM fdinfo counters are unavailable. GPU engine time is not whole-GPU utilization, and separate engine totals may exceed 100%.
- Full details: [RELEASE-V26.md](docs/releases/RELEASE-V26.md).

## 0.25.0 (experimental) - 2026-10-13
- Adds Linux DRM fdinfo per-process GPU engine busy-time sampling. This is NOT chip utilization and does not include KWin compositing or other processes. On unsupported drivers the field is unavailable. The GPU ratios of parallel engines may exceed 100% and must not be called whole-GPU usage.
- Full details: [RELEASE-V25.md](docs/releases/RELEASE-V25.md).

## 0.24.0 (experimental) - 2026-10-13
- Records the screensaver host process CPU and RSS separately from each monitor's ttfx subprocess. The GUI shows shared overhead separately and warns that summed RSS is not de-duplicated memory consumption. GPU percentage and real frames per second remain unavailable. This source is not validated on live Plasma Wayland.
- Full details: [RELEASE-V24.md](docs/releases/RELEASE-V24.md).

## 0.23.0 (experimental) - 2026-10-13
- Effect start records are emitted only when VTE reports a positive child PID. Failed spawns produce `effect_spawn_failed` records. No changes to speed scaling or actual FPS measurement are claimed.
- Full details: [RELEASE-V23.md](docs/releases/RELEASE-V23.md).

## 0.21.0 (experimental) - 2026-10-13
- Record selected effect, monitor, playback multiplier and effective `ttfx` FPS cap before each launch.
- Distinguish an FPS cap from actual rendered FPS. The latter remains unavailable.
- Show the most recent FPS cap per monitor/effect in the performance viewer.
- Full details: [RELEASE-V21.md](docs/releases/RELEASE-V21.md).

## 0.20.0 (experimental) - 2026-10-13
- Effect play buttons now open a single inline VTE terminal under the effects grid, rather than opening many separate windows.
- Stop preview destroys the terminal and cancels pending launches; selecting a different effect replaces the active preview.
- The preview uses the installed Rust ttfx and configured artwork, capped at 30 FPS.
- Full details: [RELEASE-V20.md](docs/releases/RELEASE-V20.md).

## 0.19.0 (experimental) - 2026-10-13
- This release fixes the completed-artwork fallback so it centers a multi-line logo as one visual block rather than independently centering each line. It preserves relative indentation and trailing whitespace, expands tabs at eight-column stops using terminal-cell widths, strips control characters, and clips rows/columns. This matters when an animation has finished and the monitor is waiting for the synchronized transition barrier.
- Full details: [RELEASE-V19.md](docs/releases/RELEASE-V19.md).

## Earlier tagged releases

## [0.2.0] - 2026-09-20

### Added

- A GTK 4 control panel for status, start, preview, stop, preferences, artwork,
  and installation diagnostics.
- Guided installation of missing system dependencies on Fedora/RHEL,
  Debian/Ubuntu, Arch-family, and openSUSE systems.
- AppStream metadata and a project icon for desktop integration.
- Offline TerminalTextEffects wheels in published release archives.
- `kde-ascii-saverctl doctor` for runtime, configuration, D-Bus, and watcher
  checks.

### Changed

- Use the project-controlled `io.github.robbybobby77.KdeAsciiSaver` application
  ID and migrate legacy desktop entries during upgrade.
- `kde-ascii-saverctl prefs` opens the control panel; `config` opens the raw
  JSON file.
- Manual start and preview commands now report early renderer failures.
- Configuration updates use unique temporary files and sync data before their
  atomic replacement.

### Fixed

- Wait for an XDG-autostarted watcher to release its single-instance lock
  before replacing it, and verify that its successor starts successfully.
- Align the changelog with the contents and publication date of version 0.1.0.

## [0.1.0] - 2026-08-30

### Added

- Multi-monitor animated ASCII renderer using GTK 4, VTE, and TTE.
- KWin Layer Shell overlays with an X11 fullscreen fallback.
- Native Qt 6/KF6 KIdleTime watcher for Plasma Wayland and X11.
- Safe KScreenLocker `AboutToLock`, `ActiveChanged`, and `GetActive` handling.
- Plasma user service, desktop entry, installer, uninstaller, and control CLI.
- Upgrade-safe configuration and editable Plasma ASCII artwork.
- A checksum-verifying online installer for the latest stable tagged release.
- Public installation, maintenance, troubleshooting, support, security, and
  release-acceptance documentation.
- Structured GitHub forms for bug reports and feature requests.
- Dependency guidance for Fedora/RHEL, Debian/Ubuntu, Arch, openSUSE, and
  manually packaged distributions.
- Fedora and Debian native-watcher builds in CI.
- XDG session autostart when no systemd user manager is available.
- A single-instance watcher lock and PID-based lifecycle for autostart mode.
- Unit tests for config merge, config validation, TTE restart backoff, and
  `$EDITOR` argv parsing.

### Changed

- Make the verified online installer the recommended install path while keeping
  inspect-before-run and Git-clone alternatives.
- Pin TerminalTextEffects 0.15.0 with hashes for reproducible installation.
- Resolve Python from `PATH` instead of assuming `/usr/bin/python3`.
- Report either systemd or XDG autostart integration in controller status.
- Probe GTK4 Layer Shell after GTK connects a display.
- Watcher lock failures exit 1, D-Bus `GetActive` uses a 1s timeout, and
  SIGTERM/SIGINT quit the overlay instead of relying on default terminate.
- TTE child crashes back off and give up instead of restarting every 80 ms.
- `kde-ascii-saverctl` refuses to overwrite an unreadable `config.json`.
- Require `XDG_RUNTIME_DIR` for PID and lock files instead of falling back to
  `/tmp`.
- Build the native watcher in a temporary directory and `cmake --install` into
  the data directory.
- Read the project version from the `VERSION` file.
- Validate `frame_rate`, colors, `exclude_effects`, `enabled`, and `idle_delay`
  when loading `config.json`.
- Split `$EDITOR` / `$VISUAL` with `shlex` and resolve a single token with
  `shutil.which`.
- Follow Gdk monitor add/remove while the saver is showing.
- Skip blocking `GetActive` once `AboutToLock` or `ActiveChanged` already
  reported a lock.
- Compile the watcher with `-Wall -Wextra` on GCC and Clang.
- Claim renderer and watcher PID files exclusively (`O_EXCL`, mode `0600`)
  inside `$XDG_RUNTIME_DIR`.
- Decode TTE child exits with waitpid helpers and give up after five
  consecutive failures, matching gnome-ascii-saver.
- Document default-branch-only security support and the PyPI/venv install path.

### Fixed

- Probe `GetActive` while the cached lock flag is set so a cancelled
  `AboutToLock` without `ActiveChanged(false)` cannot block idle launch.
- Fedora/RHEL dependency hint now includes `python3-pip` and `python3-devel`.

[Unreleased]: https://github.com/JustAdreamerFL/ascii-saver/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/JustAdreamerFL/ascii-saver/releases/tag/v0.2.0
[0.1.0]: https://github.com/JustAdreamerFL/ascii-saver/releases/tag/v0.1.0
