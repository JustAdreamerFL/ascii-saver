## Current UI/renderer stabilization: V107

Fedora screenshots of the V106 Preferences proved the earlier breakpoint-based design did **not** prevent clipping. V107 removes the wide navigation widget rather than trying another threshold, and makes potentially wide settings controls vertically stacked by default. The main dashboard owns running state; Preferences owns configuration. Advanced color transitions are progressively disclosed, while the main menu exposes diagnostics and editing actions. This is source- and headless-tested; real GNOME/KDE Wayland acceptance remains pending.

# ASCII Saver: active product roadmap

Updated: **2026-11-09** (V109). This is the maintained roadmap for planned work, UX
principles and milestones. It does not replace the bug register in
[MASTER-BACKLOG.md](MASTER-BACKLOG.md), the actionable checkboxes in
[TASKS.md](TASKS.md), or the dated release history in [CHANGELOG.md](CHANGELOG.md).

## V109 usability correction (2026-11-09)

The user reported that V108 still forced effect RGB to palette, cramped desktop sliders, did not adapt navigation to wider windows, lacked visible Text/Draw modes, and missed Esc handling in several top-levels. Source changes now add a saved RGB override opt-out, adaptive wide sidebar with compact selector, full-width sliders, vertically centered embedded Preview, consistent capture-phase close shortcuts and a dedicated Preferences Tools page. **Next milestone is real Fedora GNOME GTK visual and functional acceptance**, followed by KDE verification. Do not consider this UX gate completed based solely on headless tests.

## V108 stabilization gate (2026-11-09)

Core usability and quality before new features: dynamic global/per-monitor palettes and Reset, recent actually used artwork, click/drag retouch with selection editing, reliable Surprise preview, native window ownership and Esc/Ctrl+W, contextual save state and responsive dropdowns. Implemented in source with headless tests; real Fedora GNOME/KDE verification remains open. Do not mark the visual acceptance gate done until the screensaver runs on both compositors with user screenshots.

## Product principles

1. **Beginner first, powerful later.** Give a visible path to a useful result
   with sensible defaults. Show advanced parameters only when requested.
2. **Direct feedback.** Every edit or visual option has a real, promptly updated
   preview. Source and result appear **side by side** when width permits and
   **top to bottom** on narrow windows. Use responsive libadwaita breakpoints;
   do not hide functionality behind a clipped panel.
3. **Creative breadth.** Templates should inspire distinct visual directions,
   not simply offer several canvas sizes or cosmetic name variations.
4. **Explicit file ownership.** Never overwrite a source photo or artwork
   implicitly. Keep originals editable, changes reversible, and Save/Discard
   visible. Export to the renderer's existing `.txt` artwork model.
5. **Offline core.** Core editor, local templates and user assets work without
   any online service. External libraries are optional and provider failures
   cannot block local editing.
6. **No placeholder features.** A checked task represents a working source
   implementation and regression coverage. Actual GTK/GNOME/KDE verification
   remains separately unchecked until performed.

## M2: Core playback, watcher and multi-monitor reliability

**Status:** active alongside the existing Artwork Studio milestone. V101 shifts
work back toward the whole application. Do not mark live KDE/GNOME behavior as
verified solely because source tests pass.

- [x] **V101:** Honest manual Start/Preview mode checks; non-destructive
  conflicting requests; verified bounded Stop without SIGKILL; precise
  dashboard status and single-flight, time-bounded command dispatch.
- [x] **V102: Watcher ownership and stale PID recovery.** KDE now avoids
  automatic launch over an existing manual renderer and defers until it exits;
  GNOME uses held PID-file locking and verifies old watcher identity rather
  than treating any live PID as proof. Shared exact-process checks are compiled
  and exercised by both C and C++ native probes. Not a KDE/GNOME session test.
- [x] **V105: Preferences and entrypoint repair.** Fixed out-of-scope
  banner widget names, opened Preferences directly, unified command parsing
  across installed launchers and added modal Help/System Info dialogs with Esc.
  Headless regression tests passed, live GNOME/KDE verification remains open.
- [x] **V104: Cohort start scheduling and palette stability.** A single
  shared GTK callback starts the next animation round across live displays;
  initial and newly connected fullscreen monitors use bounded, round-aware
  cohort timers so stale scheduled starts cannot affect another round.
  Per-monitor palette overrides, V103 ping-pong progression and the separate
  Preview clock remain unchanged. Simulated hotplug/round tests passed.
- [ ] **V104 live monitor timing:** Verify launch skew, independent monitor
  palettes and barriers through hotplug on physical dual-display Wayland;
  GTK callback grouping is not frame-level compositor synchronization.
- [ ] **V102 native/runtime verification:** Rebuild Qt/KIdleTime and GNOME/GIO
  watch services; test competing manual/idle launches, lock/unlock, suspended
  activity, stale PID reuse and service restart on real Wayland sessions.
- [ ] **Playback runtime validation:** Test manual/automatic ownership of
  renderer, preview dismissal, idempotence, startup/shutdown timeouts, and
  normal GNOME/KDE desktop window behavior.
- [ ] **Inhibitors and activity:** Verify video/presentation and game fullscreen
  inhibition on real sessions. Investigate missing signals or watchdog bugs
  only with test evidence.
- [ ] **Multi-monitor:** Reproduce and assess synchronized vs independent
  effects, hotplug, mixed orientation and user-defined palettes with logs.
- [ ] **Performance:** Measure watcher idle CPU/RSS/PSS and renderer frame
  pacing, not speculate from old measurements.
- [ ] **UX & compatibility:** Confirm taskbar grouping, responsive settings,
  error messages and keyboard access on both Wayland desktops.

## M1: Artwork Studio and ASCII Asset Pipeline

**Status:** in progress, not scheduled for a public release. User-approved future
milestone. Implemented iteratively in experimental source releases.

### Discovery and creation

- [x] **V86: creative starter gallery.** Eight original, editable templates
  spanning cinematic landscape, sci-fi diagrams, botanical art, neon
  typography, minimalist waves, pixel architecture, geometric patterns, and
  playful retro arcade. Searchable picker, per-template preview, responsive
  side-by-side/stacked layout, explicit choice and no silent file writes.
  **Real GTK UI validation pending.**
- [x] **V87: Photo to ASCII.** Import a local PNG/JPEG/WebP/BMP, choose center
  crop or fit/pad, tune the 16–120 by 8–60 terminal-cell canvas with a
  physical glyph aspect ratio, and generate editable monochrome ASCII.
  The source photo remains untouched. Live GTK validation pending.
- [x] **V87: Responsive comparison.** Original image beside ASCII output,
  automatically stacked on a narrow window; changes redraw after an 80 ms
  debounce. GUI layout needs actual Wayland verification.
- [x] **V87: Basic conversion controls.** Brightness, contrast, invert,
  three distinct character ramps, dimensions and framing, with sensible
  defaults. Advanced controls are still pending.
- [x] **V87: Safe save/export.** Explicit Save as New Artwork creates a unique
  `.txt` file in the existing local library without overwriting existing art.
  Use in Editor respects the existing unsaved-edit confirmation. Exported files
  are accessible through the existing artwork picker; user verification pending.

### Advanced tools, revealed progressively

- [x] **V88: Collapsed Advanced image tools.** Gamma (0.5–2.5),
  localized edge definition (0–100), and optional Floyd-Steinberg dithering
  with a one-action reset. These controls share the existing debounced live
  preview; their neutral defaults preserve the V87 artwork output.
  Regression-tested with uniform tones, edges, gradients and padded photos.
  **Real GTK/Wayland preview and accessibility verification pending.**
- [x] **V93: Posterization and RGBA compositing.** A collapsed Advanced
  choice limits tone levels to 2–8 (or leaves them unmodified); transparent
  PNG/WebP backgrounds may composite on white, gray or black instead of always
  white. The matte control is disabled for images with no alpha channel.
  Changes use the existing live preview and are stored in every new photo
  project or reusable preset. Old V89/V91 files remain loadable with neutral
  defaults, and existing artwork stays unchanged until explicit export.
  Pure headless regression tests pass; real GTK visual assessment remains open.
- [ ] Further polish: optional blur or distinct sharpening styles, only if
  genuinely helpful beyond the existing edge definition. Do not confuse
  edge-definition with an edge-only conversion.
- [x] **V94: safe custom ASCII ramps.** The basic style menu now includes
  Custom. Selecting it expands Advanced and reveals a 2–63-character ramp
  entry ordered from dark to light, with an implicit lightest space. Only
  distinct printable ASCII 33–126 are accepted: no tabs, Unicode width
  ambiguity, ANSI escapes or control codes. The live comparison and preset/
  photo-project workflows use these symbols end to end. Changing back to a
  built-in ramp restores rendering if a custom string is unfinished. The
  existing renderer supports plain ASCII text, but **physical GTK/VTE
  confirmation remains open**.
- [ ] ANSI-color output only after renderer/VTE validation and a complete
  export/data model; do not mix escape sequences into the existing .txt format.
- [x] **V89: Non-destructive photo project persistence.** Exporting a new
  photo artwork keeps its original source bytes and a versioned validated
  conversion recipe in `photo-projects/<artwork-stem>/`, separate from the
  renderer `.txt` asset. From Artwork Editor, Reopen Photo restores the
  original picture and all basic/advanced controls; a modified hand-edited
  `.txt` is detected and identified as separate from the recipe. Save as New
  makes a new project/asset variant without overwriting either old text or
  source. File writing uses exclusive creation and cleans up failed writes.
  All project contents are local and usable offline. GTK live testing pending.
- [x] **V96: Manual ASCII retouch.** Retouch is discoverable in the existing
  native Artwork Editor but does not clutter the default editing surface.
  Choose a printable ASCII ink, paint or erase one character at the caret,
  or select any text region to mirror horizontally (including facing slashes
  and brackets) or flip the selected rows vertically. Tools use the Gtk
  TextBuffer's limited native Undo/Redo history, and Save remains explicit.
  No action writes the original artwork until Save. Pure transforms, invalid
  characters, file ownership and UI source integration are regression-tested.
  **GTK keyboard/focus and narrow-window visual validation still pending.**
- [x] **V97: Mouse-driven ASCII canvas.** Artwork Editor has a separate
  **Draw on Canvas** mode with a fixed-width character-cell grid, live brush
  path feedback, one-character ink, eraser and continuous left-button drag.
  Fast strokes are interpolated across intermediate grid cells; each gesture
  commits to the existing Gtk.TextBuffer as one grouped Undo step. Mouse and
  Text modes share Save and the unsaved-close confirmation. The canvas accepts
  only bounded plain printable ASCII (200 columns / 100 rows maximum); Unicode,
  tabs and oversized files remain safely editable in Text mode. The canvas
  is not a bitmap export or a new file format. Source tests pass; actual GTK
  pointer capture, scrolling and focus require live validation.
- [x] **V98: Canvas viewport and control refinements.** Responsive
  brush/erase/zoom/grid controls, bounded 75%-200% zoom and a cosmetic grid
  toggle without changing the artwork buffer. Pointer mapping uses the same
  Pango-measured logical character cells as drawing, not an extra device-scale
  multiplication. Zoom attempts to retain the top-left visible character as
  GTK readjusts scroll bounds. Ctrl+Z / Shift+Ctrl+Z / Ctrl+Y operate on the
  shared history with the Canvas focused. In-progress strokes are discarded
  when changing zoom or leaving Canvas. Automated tests pass; actual GTK
  fractional scaling, scrolling and keyboard input remain unverified.
- [x] **V99: Keyboard Canvas and minimal text edits.** Arrow keys move an
  on-canvas focus cell, Space paints and Delete/Backspace erase, all using the
  existing brush, one-action native Undo and explicit Save. Keep the active
  cell in view while scrolling, share the current hint line for location
  feedback, and do not intercept normal Tab navigation. Update only the
  changed Gtk.TextBuffer range, suppress transient refresh during its grouped
  modification and redraw once on completion. Pure geometry and fake-buffer
  tests pass; real GTK focus, high-DPI scroll and keyboard accessibility
  still need GNOME/KDE verification.
- [x] **V100: Non-destructive work-area sizing and viewport drawing.**
  A compact Canvas popover allows explicit 48-200 column / 18-100 row grids
  without padding the stored `.txt` with empty cells. Fit to artwork only
  reduces unused virtual grid, never crops content. Mouse and keyboard can
  paint beyond the original default grid. For larger art, redraw only visible
  rows, columns and in-progress brush marks, plus one guard cell. These are
  source-tested; actual GTK/Wayland scrolling and focus remain unverified.
- [ ] Rectangle selection, multi-cell brush sizes and layers remain deferred
  pending real GTK/Wayland user testing; do not add unvalidated controls.
- [x] **V90: Offline local gallery.** My Artwork lists existing `.txt`
  assets and linked Photo to ASCII projects with bounded real ASCII text
  thumbnails, names, measured dimensions, source and shape. Search names/tags,
  filter by text/photo and landscape/square/portrait, clear filters, and open
  an asset in its own safe editor without replacing another unsaved buffer.
  Optional tags are explicit, validated and stored as separate atomic JSON
  metadata. Copy any original creative template to a personal `.txt` with
  collision-safe Save a Copy. Real GTK/Wayland use remains unverified.
- [x] **V91: Creative Photo Looks & reusable presets.** Six built-in looks
  are deliberately visually different (classic terminal, high-contrast noir,
  wide soft landscape, high-contrast graphic poster, retro chunky arcade,
  and fine architectural detail). Apply updates the existing live preview and
  all editable controls, without touching the source photo or saving artwork.
  Personal conversion settings can be saved under unique names, loaded and
  removed with confirmation in a collapsed **My conversion presets** section.
  The preset library is offline, versioned, size-bounded and rejects corrupt
  or symlinked files; built-in looks are immutable. Source-level tests passed.
  **Still requires live GTK visual, keyboard and usability testing.**
- [x] **V92: Artwork Details and provenance.** Creator, description,
  source HTTPS URL, user-stated license and tags, using an atomic V2 sidecar
  that reads legacy V1 tags without changing renderer `.txt` files. Never
  invent the creator or claim a verified license for an online import.
- [ ] Color or animation filters only after real supported asset formats
  exist and they work in the renderer and library.

### Optional online art gallery

- [x] **V92: first optional provider, ascii-bin.** Fetch its public
  `asciiart_db.txt` over HTTPS on explicit Browse Online. Use the documented
  `===EOF===`, `tags:`, `description:` text feed; bound size, geometry and
  control characters. Display real previews, name/tag search, shape filters,
  source URL, and an explicit import confirmation. Save provenance and copy
  each selected artwork without touching existing files.
- [x] **V92: offline fallback.** Private, size-bounded cache is updated only
  after parsing succeeds; offline shows cached entries or an error without
  interrupting local editing. Network happens on a worker thread.
- [x] **V95: responsive online discovery at scale.** Browse Online now
  limits its initial remote rows to 48, incrementally appending more only when
  requested. Search and filters remain instant with total counts. Sort by title
  or measured character-cell area, or use Surprise Me to shuffle the loaded
  collection without a network request; the random order is stable across
  pages. Refresh runs one request at a time and retains already loaded art if
  a later refresh fails. Live GTK/Wayland and actual HTTPS operation remain
  separately unverified.

- [ ] **Licensing caveat:** The ascii-bin repository claims CC0 on the
  compilation, but explicitly cannot waive original creators' rights.
  Every imported piece retains a *claims CC0, rights unverified* warning;
  do not assert verified authorship or permitted commercial redistribution.
  Additional sources require distinct provider validation and licensing.
- [ ] Live GTK desktop and remote HTTPS validation on GNOME and KDE Wayland;
  current offline tests use an injected documented-format feed.
- [ ] Optional publishing/submissions are a separate decision, not part of M1.

### Definition of done

A first-time user can start from one of genuinely different visual styles **or**
a photo, understand the result through a responsive live comparison, safely
save a new piece of art, reopen it and use it within ASCII Saver. Advanced
options remain discoverable without crowding the entry workflow. Optional remote content retains its unverified-rights warning and works
safely when offline. Mark the milestone done only after GNOME and KDE runtime tests.

## M0: existing behavior and GNOME/KDE validation

Source-level fixes through V85 cover responsive Preferences, the library and
playlist editors, multi-monitor persistence, palette-aware effects and
source-level window identity. Real KDE taskbar grouping, GNOME cursor/lock
stacking, fullscreen dismissal, two-monitor rendering and responsive windows
remain **unverified**. See [TASKS.md](TASKS.md) for the exact testing queue.

## Longer-term, separately deferred

- KScreenLocker / wallpaper integration with no authentication regressions.
- More advanced transitions between user-defined palettes, deferred by user.
- Additional desktop backends only with complete, supported implementations.

## Documentation map

- **[ROADMAP.md](ROADMAP.md):** product direction, UX, future milestones.
- **[TASKS.md](TASKS.md):** concise status checkboxes and current validation.
- **[MASTER-BACKLOG.md](MASTER-BACKLOG.md):** fully indexed historical issues.
- **[CHANGELOG.md](CHANGELOG.md):** dated implemented changes.
- **`RELEASE-Vxx.md`:** source-level verification and notes for each release.
- **`docs/archive/UX-ROADMAP-V54.md`:** original UX priorities retained verbatim.
- **`RENDERER-BACKLOG.md`, `BACKLOG-V55.md`, `OBSERVATIONS-*.md`:** technical
  evidence and original reports. These are maintained as historical evidence,
  not competing active task trackers.


V103: Optional ping-pong palette progression (first → last → first) with existing per-monitor overrides and synchronized effect rounds. Desktop validation pending. See RELEASE-V103.md.
