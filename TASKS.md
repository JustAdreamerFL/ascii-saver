# ASCII Saver: current checklist

Updated: 2026-11-09, V109. Source checks are **not** visual Wayland acceptance.

## V109: targeted Fedora fixes, source complete and live UI not verified

- [x] Add an opt-out from palette overriding per-effect RGB across fullscreen and every real Preview window; persist `override_effect_colors` through Save/Discard and reload.
- [x] Compact section selector below 900sp, synchronized wide sidebar above; move all Tools into Preferences, keep Preview behavior separately.
- [x] Eliminate slider side-by-side row squeezing on desktop, use full-width controls with right-hand current value and existing defaults reset actions.
- [x] Capture Esc, Ctrl+W and Ctrl+Q on Preferences, Playlists, Artwork Editor, Effect Library and extra editor windows while honoring unsaved confirmations.
- [x] Explicit Text/Draw choice and Draw-first initialization on compatible ASCII artwork; preserve canvas gesture callbacks and text mode.
- [x] Center bounded inline Effect Library VTE vertically without stealing card scrolling height.
- [x] Headless regression suite, install manifest, effect packs and cumulative archive checks.
- [ ] **Fedora live acceptance REQUIRED:** confirm RGB preservation when override disabled, sidebar at 900/1200sp, sliders, centered inline preview, close shortcuts and painting/typing on real GTK Wayland.
- [ ] **KDE live acceptance REQUIRED:** repeat window shortcuts, stacking and color behavior; source checks cannot establish compositor-specific behavior.

## V108: Fedora quality stabilization

- [x] Dynamic palette size (1–8 colors): Add / Remove last / Restore default, and update Reset availability after a manually edited swatch.
- [x] Toggle per-display palettes without toggling per-display FPS/artwork; provide per-display Add/Remove/Reset and save state independently.
- [x] Recent local artwork history begins tracking on successful renderer starts and exposes the editable default artwork in My Artwork.
- [x] Canvas click and drag painting, selected-text Paint/Erase and shared Undo/Redo, with Draw first when compatible.
- [x] Online Surprise picks a real matching selection even outside the initially loaded page and updates list/preview state.
- [x] Adwaita Preview title, application identity and Esc/Ctrl+W/Ctrl+Q; transient Effect Library/diagnostics/photo/artwork/measurement windows with close keyboard handling.
- [x] Centered, min-width dropdown entries in Effect Library/Playlist Editor; inline Effect Preview centered inside its viewport and cleaned up when stopped.
- [x] Hide clean Preferences Save/Discard footer, reduce permanent explanatory prose, keep large-width adaptive breakpoint.
- [x] Headless behavior, install manifest and regression checks.
- [ ] **Fedora live acceptance:** Verify palette saving/refresh, Draw click/drag at fractional scaling, Surprise on a large loaded collection, all dialogs and focus, max/narrow sizes and actual terminal centering.
- [ ] **KDE live acceptance:** Verify native Preview window grouping, Esc/close and Effect Library task-switch behavior.
- [ ] Assess actual saved-state behavior under repeated closing of multiple editors and when a palette chooser dialog is open.

## V107: HIG / responsive Preferences redesign (reported with screenshot)

- [x] Remove five-titlebar-tabs minimum-width trap; use one synchronized category selector.
- [x] Keep special controls and per-monitor controls on their own full-width line, including font, palette and numeric controls; no dependency on a breakpoint to avoid clipping.
- [x] Remove live renderer/watcher process states and diagnostic cards from Preferences; preserve dashboard status and expose diagnostic/editing tools from application menu.
- [x] Make palette transitions an optional expander, preserve cycle/ping-pong and monitor settings.
- [x] Hide clean “Changes saved” footer; show Save/Discard only when dirty in bottom bar; messages use toast.
- [x] New source regression tests, Python syntax, CLI/installer/asset checks.
- [ ] **Fedora GNOME visual QA:** actual 360, 420, 600 logical pixel windows, long font names, monitor palette/artwork rows, active selector and Save/Discard.
- [ ] **KDE Wayland visual QA:** same scenarios, Alt-Tab/taskbar and Esc for Diagnostics.

## V106: direct Fedora GUI feedback

- [x] Remove duplicate Close action from dialog header and retain Esc behavior (source tested).
- [x] Share desktop identity between Preview renderer and GUI, without sharing a D-Bus singleton (source tested).
- [x] Make multi-color palettes cycle by default, migrate ambiguous pre-V106 false defaults, persist explicit static preference with `palette_mode` (behavior tests).
- [x] Reflow long controls vertically on compact Preferences; replace overlapping unsaved overlay with stable bottom tray (source tested).
- [ ] **Fedora visual acceptance test:** Confirm no duplicate close, correct preview Dock/Alt-Tab grouping, color changes after two successive successful effects, and no clipping when width is 350 to 620 pixels.
- [ ] **KDE Wayland check:** Verify window identity, settings width and palette after upgrade separately from Fedora.

## V105: Preferences and consistent commands

- [x] Correct unsaved banner widget lifetime across Preferences shell methods;
  remove the undefined name references that caused startup to fail.
- [x] Route direct Preferences requests without raising Dashboard; unify
  `ascii-saver`, `ascii-saverctl` and `ascii-saver-settings` through one
  CLI dispatcher, preserving renderer flags and `start` semantics.
- [x] Add modal Help and System Information windows with Esc and Close.
- [ ] **Fedora Wayland validation:** Fully exit existing GUI process and
  launch Dashboard, Preferences and menu dialogs; verify Alt-Tab, Escape,
  old launcher aliases and a real fullscreen/Preview start/stop.

## Core synchronization, palettes and hotplug (V104)

- [x] **Single fullscreen cohort start:** Shared playlist/effect/palette round
  advances only after all live monitors finish and hold their final frame.
  Schedule one next-round GTK main-loop callback for the whole cohort instead
  of one independent timer per display (source tested).
- [x] **Round-aware hotplug:** Group the first launch and newly connected
  fullscreen monitors, and ignore timers for old rounds, removed windows or
  shutdown. A live monitor's running effect must not be restarted by hotplug.
- [x] **Preserve palette clocks:** V103 bounce/cycle, independent per-monitor
  color overrides, synchronized fullscreen rounds and standalone Preview
  remain unchanged. Simulated two-monitor test includes different colors.
- [ ] **V104 physical verification:** Compare logs and visible start timing on
  two monitors, with different refresh rates, hotplug before first spawn and
  during final-frame hold, plus shared/unshared effects and V103 palettes.
  Grouping timers does not guarantee frame-identical VTE child render starts.

## Implemented in source (runtime confirmation still required)

### Idle watcher ownership and recovery (V102)

- [x] **KDE watcher / manual playback:** Before an automatic idle launch, check
  the existing renderer PID file against the current user's exact `app.py`
  command, not just this watcher's own `QProcess`. Defer rather than start a
  duplicate if a manual fullscreen or Preview already owns the renderer;
  recheck on deferred poll and cancel on resumed activity.
- [x] **GNOME watcher / stale PID:** Hold a nonblocking lock on the native
  watcher's PID inode for its lifetime. Do not treat an unrelated process that
  reused an old PID as another native watcher; refuse to replace a verified
  running legacy watcher and unlink only our own locked inode at shutdown.
- [x] **Shared process identity:** Compile the same strict, bounded Linux
  PID/`/proc` helper in C and C++, with live-process and malformed-file tests.
  The GNOME watcher also reuses the exact-script check for active renderers.
- [ ] **V102 live verification:** On actual KDE and GNOME, test auto-idle while
  manual Preview is open, closing Preview without new input, user resume,
  lock/unlock, and deliberate stale PID recovery during startup. Rebuild both
  native binaries with Qt/KIdleTime and GIO/JSON-GLib before claiming runtime
  validation. Note: no monitor scheduling or Rust renderer changes in V102.

### Core screensaver playback and dashboard (V101)

- [x] **V101: Safe Start/Preview lifecycle.** Detect the existing renderer's
  mode before handling manual start requests. Reject the opposite mode rather
  than showing a false success or silently taking over the active session.
- [x] **V101: Verified Stop.** Use identity-checked SIGTERM, wait for the
  renderer to stop for up to 2.5 seconds, and report a failure without
  force-killing it if that does not happen. Distinguish stopped, preview and
  fullscreen in status and CLI output.
- [x] **V101: Dashboard serialization.** Start Now and Preview/Close Preview
  stay disabled while either command is pending. Bounded command execution
  and explicit failure text are handled in a separate tested module.
- [ ] **V101 live verification:** Test opening/closing Preview, full-screen
  launch, commands racing with an externally-started watcher renderer and
  forced unresponsive process behavior on real KDE/GNOME Wayland.


- [x] **E05** Separate Save/Discard in Effect Library and Playlist Editor (V74).
- [x] **E01/E03/E04** Gallery-first Playlist Editor, clearer thumbnails, search and filtering (V75).
- [x] **C01/B210** Grouped measured durations and clearer CPU/RAM/GPU/FPS graphs (V76).
- [x] **D01-D04/T02** Centered preview, Replay and final-frame cursor cleanup (V73/V77).
- [x] **C02/C03** Diagnostics dialog and honest artwork save/close feedback (V78).
- [x] **B01/B02** Adaptive Preferences navigation and Save/Discard (V79).
- [x] **B206-B208** Shared/independent monitor auto-fit behavior and restoring font when disabled (V69).
- [x] **B209** File-based artwork picker and editor (earlier releases).
- [x] **B214** One library-owned preview mode control (V81).
- [x] **A05** Long dashboard status text is single-line and ellipsized with full tooltip, instead of resizing the card (V83; live UI still needs confirmation).
- [x] **B212 (clarity)** Separate dashboard status for automatic idle activation from watcher process and manual playback; Configure opens existing activation settings (V82). The watcher process itself is **not** toggled by this button.
- [x] **D05** Suggested duration/intensity text visible on every effect card in both Effect Library and Playlist Editor (V82).
- [x] **UX responsive galleries**: Effect Library's grid wraps from 1 to 3 columns; both libraries adapt search/filter controls and offer Clear filters in a no-match state without altering selection (V85, source-level, live visual review pending).
- [x] Per-monitor controls added and removed when display topology changes, preserving disconnected and unsaved values (V80).
- [x] Playback scheduling isolation, randomization and multi-monitor synchronization logic (V68).
- [x] Palette applies to effects' output as well as animated sample thumbnails (V70-V72).
- [x] Version/date history maintained in `CHANGELOG.md` and `RELEASE-Vxx.md` (V81+).

## Artwork Studio milestone: explicitly requested, in progress

For scope, UX rules, creative template styles, responsive live comparisons,
image-to-ASCII conversion, advanced tools and future online browsing, see
[ROADMAP.md](ROADMAP.md). The historical issue register remains separate.

- [x] **M1.1** Original templates in eight distinct visual styles, searchable
  preview picker, responsive comparison and explicit Use Template (V86).
  Source-level tests only; live GTK validation pending.
- [x] **M1.2** Photo to ASCII: local PNG/JPEG/WebP/BMP import, character-cell
  aspect ratio, center crop / fit, bounded image decode, live source/result
  comparison with responsive layout (V87). GTK live validation pending.
- [x] **M1.3** Basic width/height, brightness, contrast, invert and style
  controls; explicit unique Save as New Artwork into the existing local
  collection or Use in Editor with discard confirmation (V87, source tested).
  Reopen via existing artwork picker must still be confirmed on the desktop.
- [x] **M1.4a** Collapsed Advanced photo controls: gamma, edge definition,
  Floyd-Steinberg dithering and Reset, sharing the live comparison (V88).
  Source-tested only; actual GTK usability/accessibility remains unchecked.
- [x] **M1.4b** Reopen editable Photo to ASCII conversions (V89):
  Save as New stores the original image bytes, the complete conversion recipe
  and checksums beside a new `.txt` artwork. **Reopen Photo** restores the source
  and controls from the Artwork Editor. If text was manually edited, warn that
  the photo recipe will not recreate those hand edits. Each revision exports
  as a new variant; stored sources and existing artwork are never overwritten.
  GTK live confirmation still required.
- [x] **M1.4c / V90** Offline My Artwork gallery: real ASCII text thumbnails,
  name/tag search, source and orientation filters, Clear Filters, separate
  Open Artwork, explicit per-asset tags and Save a Copy from original templates.
  No read-only browsing action changes an unsaved editor buffer. Headless
  source/metadata/invalid-file tests passed; real GTK validation outstanding.
- [x] **M1.4d / V91** Six curated, distinct Photo to ASCII conversion looks and
  reusable named custom presets. Apply, Save Preset and confirmable Remove
  operate only on settings; validation and exclusive creation prevent corrupt
  recipes, unsafe paths and overwrites. Built-in looks remain immutable.
  Source-level regressions passed; live GTK usability/keyboard testing pending.
- [x] **M1.4d continued / V93** Posterization (off or 2–8 distinct luminance
  tones) and a white/gray/black matte for transparent pixels, under collapsed
  Advanced image tools. Both use the existing responsive live preview, Reset,
  Save as New Artwork and reusable presets. V89/V91 saved recipes missing the
  new settings load with the original defaults. Pure conversion and source-level
  UI tests passed; live GTK confirmation pending.
- [x] **M1.4d / V94** Custom printable ASCII character ramps (2–63 unique
  symbols, dark to light, with an implicit blank). Optional entry stays hidden
  under Advanced until **Custom** style is selected; this expands the section.
  Inline invalid-input status clears the stale preview and disables export.
  Older projects/presets without the field remain readable; the three built-in
  ramps are unchanged. Source-level conversion, persistence and UI contracts
  tested; actual GTK/VTE glyph/caret/keyboard verification remains unchecked.
- [ ] **M1.4d further polish** Optional blur or distinct sharpening modes,
  only if they produce useful results beyond the existing edge definition.
- [x] **M1.4e / V92** Optional local Artwork Details: tags, creator,
  description, stated license, and HTTPS source link, all stored in the
  existing metadata sidecar, with automatic read support for V90 tag-only
  records. Renderer `.txt` files are never edited by metadata updates.
  Metadata is user-supplied, not independently rights-verified.
- [x] **M1.5 / V92 (first provider)** Opt-in Browse Online integrates the
  public ascii-bin text collection: search, tags/orientation filters, real
  text preview, explicit Import a Copy, provenance and rights warning, and
  a limited cached offline copy. The repository claims CC0 but cannot verify
  individual contributors' rights. No login, publishing or background
  downloads. GTK and real remote network still require on-device tests.
- [x] **M1.5 UX / V95** Online Explore gallery now paginates at 48 cards
  per batch (Show More without scroll/selection reset), orders by repository,
  title, size, or shuffled discovery, and offers Surprise Me without another
  network request. Refresh is single-flight, import is disabled during load,
  a failed refresh preserves already loaded in-memory artwork, and the active
  tag survives updates when available. Headless sorting, paging and UI-source
  contracts passed. Actual GTK/Wayland/network validation remains open.
- [x] **M1.6 / V96** Manual retouch in the existing Artwork Editor:
  caret-based Paint/Erase with a small glyph palette and one-character ink,
  selected-text horizontal Mirror/vertical Flip, plus native GTK Undo/Redo.
  All operations change only the unsaved text buffer. Large/invalid selections
  and control-character ink are rejected. Automated core and integration
  tests passed; live GNOME/KDE focus, keyboard and responsive UI tests pending.
- [x] **M1.6 continued / V97** Optional Draw on Canvas mode with visible
  grid, hover indication, live drag strokes, continuous interpolated paint,
  a single-character ink and Erase. One gesture is one grouped native GTK
  Undo step; it updates the exact Text buffer used by Save and close/discard.
  Unsupported Unicode, tabs and out-of-range artwork are never modified by
  canvas mode, but remain accessible in Text mode. Headless rendering-source,
  canvas geometry, brush/eraser and direct buffer tests passed. Live GTK mouse
  input, canvas scroll, undo/redo, narrow layout and high-DPI sizing pending.
- [x] **M1.6 refinement / V98** Zoom and responsive Canvas controls:
  75%-200% display-only zoom, optional character-cell grid, Pango-measured
  logical-pointer hit mapping, bounded scroll restoration after zoom, and
  wrapping tool groups in narrow windows. Canvas can receive keyboard focus
  for Ctrl+Z, Ctrl+Shift+Z and Ctrl+Y using the shared undo/redo buffer.
  Zoom or returning to Text cancels a pending stroke without saving.
  Source/headless tests pass; fractional scaling, real GTK scrolling and
  keyboard focus still need actual GNOME/KDE validation.
- [x] **M1.6 refinement / V99** Keyboard navigation on Canvas (arrow keys),
  paint via Space and erase via Delete/Backspace, active cell indication,
  clamped scroll-to-cursor and shared Undo/Redo. Canvas commits now change
  only the necessary Gtk.TextBuffer range and refresh once after the entire
  undoable user action, preserving the active drawing cursor and other text
  marks. Headless unit and fake-buffer regression tests passed. GTK keyboard,
  high-DPI scrolling and screen-reader testing remain open.
- [x] **M1.6 refinement / V100** A non-destructive Work area popover
  expands the virtual ASCII drawing grid up to 200 columns by 100 rows and
  fits back to existing content without deleting artwork or saving empty
  cells. Mouse and keyboard painting can use the expanded area. The GTK
  viewport renders only visible text/grid/brush cells for large artworks;
  pure geometry and fake-view drawing regression tests pass. Native GTK
  popover, high-DPI, scroll and cursor precision need desktop verification.
- [ ] **M1.6 later** Rectangle selection, layered editing and extra brush
  shapes require runtime evidence; not part of V97.
- [ ] **M1.5 continued** More providers only with a documented feed and
  credible per-artwork licensing; individual author provenance or verified
  license must not be inferred from repository-wide claims.
- [ ] **M1.4e continued** Color/animation filters only after those asset
  types actually work end to end.
- [ ] **M1 validation** V96 retouch and V97-V100 mouse/keyboard canvas pointer dragging, Undo/Redo, scrolling, keyboard focus and narrow controls; real GNOME/KDE window resizing, unsaved-text safety,
  keyboard access export/reopen of artwork, and V90 library filtering, opening and tags; V91 preset selection; V92 metadata editing, remote refresh, offline cache and import.

## Still open: real GNOME/KDE verification (highest priority for testing)

- [ ] **E02/B213** (runtime) Verify KDE Task Manager shows and groups the Playlist Editor and Effect Library under ASCII Saver after the V84 source correction; do not claim success without live KWin evidence.
- [ ] Confirm fullscreen Escape/pointer dismissal, cursor visibility and live preview persistence on GNOME and KDE.
- [ ] Confirm independent/shared monitor resizing, portrait/landscape auto-fit, including the old font-size ~52 crash report.
- [ ] Confirm synchronised playback, different per-monitor palettes, correct last frames and random effect order.
- [ ] Validate V74-V85 changed GTK/libadwaita layout, Save/Discard, cards, diagnostics, and monitor hot-plug in real sessions.
- [ ] **V85 UX**: On narrow windows, verify 1/2/3-column library wrapping, non-clipped Search/duration/intensity controls and empty-results Clear filters in both editors; check that selection and pending Save/Discard stay unchanged.
- [ ] GNOME cursor hiding with actual Shell/extension setup; verify Dash to Dock stacking after lock/unlock separately.

## Further user-reported improvements, not required for this release

- [ ] **B212 (optional)** Consider a dedicated start/stop watcher-service control, but only after distinguishing service lifecycle from the existing automatic-activation preference.
- [ ] **B202** Visually verify slider current-value placement above its thumb (code uses Gtk.PositionType.TOP).
- [ ] **A05/B211** Verify V83 bounded dashboard status and lack of redundant inline command logs on the real desktop.

## Deferred by request or lacking current evidence

- [ ] Advanced transitions between **different** user-defined palettes (idea deferred by user).
- [ ] KScreenLocker/wallpaper integration (future milestone; preserve secure authentication).
- [ ] Reopen the old idle CPU ~8% report only if a fresh measurement reproduces it; not a confirmed current failure.

The original observations and historical roadmaps are retained for context. See [MASTER-BACKLOG.md](MASTER-BACKLOG.md) for their full reconciliation; old unchecked boxes reflect historical snapshots, not current status.


V103: Optional ping-pong palette progression (first → last → first) with existing per-monitor overrides and synchronized effect rounds. Desktop validation pending. See RELEASE-V103.md.
