## V109 reported Fedora regressions (source fixes done; runtime validation open)

- [x] Add explicit Save-able `override_effect_colors` so the user can preserve original RGB/ANSI colors from effects rather than being forced through the user palette. Default preserves legacy override.
- [x] Adapt navigation to narrow dropdown vs wide sidebar and keep special controls/GTK sliders full-width at desktop sizes.
- [x] Put tools in Preferences, without duplicate main-menu Tool shortcuts. Center inline preview within bounded scroll area.
- [x] Use capture-phase Esc/Ctrl+W/Ctrl+Q window handler, including Preferences, Playlist and Artwork Editor. Keep close veto for unsaved content.
- [x] Expose both Text and Draw as explicit editor modes and preserve existing canvas operations.
- [ ] Actual Wayland/GTK verification of every above item, especially color output from Rust ttfx, VTE vertical alignment, pointer gesture delivery, editor focus and keyboard capture while popovers are open.

## V107: Preferences HIG redesign after narrow screenshot (2026-11-09)

- [x] Replace squashed header/bottom tab widgets with a single category selector on five native libadwaita pages.
- [x] Move long control suffixes below their titles by default, including per-monitor dynamic controls, rather than depending on breakpoints after minimum-width negotiation.
- [x] Reduce General settings to activation; renderer/watch status is on the dashboard and advanced tools in its application menu.
- [x] Collapse rarely changed palette transitions; dirty Save/Discard appears only while editing.
- [ ] Actual GNOME/KDE narrow-window screenshots, keyboard focus, GTK theme scaling, diagnostics and palette usability still to verify. V106 narrow visual acceptance **failed**, do not mark that item as accepted.

## V108 source fixes, live QA outstanding

- [x] Editable global and per-display palettes, bounded Add/Remove/Reset, true independent palette option, persisted changes and static/cycle compatibility.
- [x] Recently-used artwork list populated from successful renderer starts; Canvas click/drag and selection retouch; Surprise Me selection now on-screen.
- [x] Native titled Adwaita Preview and common close shortcuts, transient Effect Library, centered inline VTE and centered filter dropdown entries.
- [ ] **Fedora acceptance:** palette, editor gestures/selection and save, surprise selection, app identity, fully adaptive widths, no persistent saved footer.
- [ ] **KDE acceptance:** Preview Alt-Tab grouping, child windows/closing, multi-display palettes and watcher/inhibitor interactions.

## V106 direct Fedora feedback (2026-11-09)

- [x] Source fix for duplicate Close buttons in app Help/System Information dialogs.
- [x] Source fix for Preview app identity using a non-unique renderer with matching GUI application ID.
- [x] Source fix for palette cycling default/migration and explicit static-state persistence.
- [x] Source fix for narrow Preferences row reflow and non-overlapping Save/Discard tray.
- [ ] End-to-end Fedora GNOME and KDE screenshot/manual verification. The V106 implementation is **not** a visually accepted fix yet.

# ASCII Saver: full historical issue register

Updated 2026-11-08 for experimental V105. This **expands**, but does not replace, [TASKS.md](TASKS.md), which is the short working queue.

## How to read the statuses

- `[x]` **Implemented in source**: code or UI was changed and covered by offline checks. Not a claim of a successful live KDE/GNOME test.
- `[ ]` **Open or unverified**: either a currently missing feature, a reported runtime problem requiring user confirmation, or an incomplete design task. Each entry says which.
- **Deferred** means an idea or future milestone, not something to implement automatically. Historical proposals are not approvals to ship new controls.
- Source: [OBSERVATIONS-COMBINED.md](OBSERVATIONS-COMBINED.md) (A–F and B201–B214), [BACKLOG-V55.md](BACKLOG-V55.md), [RENDERER-BACKLOG.md](RENDERER-BACKLOG.md), [UX-ROADMAP.md](UX-ROADMAP.md), and release notes V19–V82. Older lists reflect their own version, not today’s status.

## V105: Reported Preferences and command-line defects

- [x] Preferences constructor referenced nonlocal `banner_label` and
  `banner_discard`, raising NameError when the window was first requested.
  Kept the banner widgets on `self` and added a regression guard.
- [x] Unified installed CLI help and commands, supported direct dashboard,
  preferences, playlist, renderer and diagnostics launches; corrected
  advertised GNOME/KDE support, desktop entry and historical wrapper aliases.
- [x] Shared Help/System Information dialog builder uses transient modal
  Adw.Window with Escape and Close button.
- [ ] Confirm real Wayland dialogs, switcher window visibility, background
  renderer Start/Preview/Stop and CLI upgrade on Fedora and KDE/GNOME.

## V104: Shared monitor cohort timing (source only)

- [x] First fullscreen monitor launches and each completed synchronized round
  now use a grouped GTK timer callback; all live monitors share an intended
  round and per-monitor colors are derived from that round.
- [x] Obsolete scheduled callbacks ignore removed monitors, shutdown and
  round changes. Hotplugged monitors join without restarting running effects.
- [ ] Physically test mixed-refresh-rate monitors, V103 bounce palettes,
  timing, hotplug and inhibition on both KDE and GNOME Wayland.

## V101-V102: Core playback, watchers and ownership

- [x] **V101 source:** Explicit fullscreen/Preview mode checking; Stop waits
  for the original verified renderer to exit before reporting success; UI
  playback actions are serialized with time-bounded command execution.
- [x] **V102 source:** KDE automatic watcher no longer starts over a running
  manual renderer. GNOME native watcher now locks its PID file through its
  lifetime and ignores unrelated reused PIDs while protecting active old
  watcher instances. Shared helper identity is tested by actually compiling
  C and C++ programs and launching live mock renderer processes.
- [ ] **V101-V102 native/runtime:** Confirm both watcher binaries compile and
  operate under actual desktop service managers. Verify idle/Preview conflicts,
  stale PIDs, lock/unlock, inhibitors and monitor behavior on GNOME/KDE Wayland.

## Main window and general behavior (A)

- [x] **A01** Shorter application identity: current application is **ASCII Saver** (V60 onwards). The original KDE AC name was a suggestion, not an approved final name.
- [ ] **A02** Idle UI CPU was reported at about 8–8.2% in V53, but a later report said it was no longer reproduced. **Do not optimize speculatively; reopen only after a fresh measurement.**
- [x] **A03** Main Preview is a persistent playback-sequence window distinct from dismiss-on-activity fullscreen mode (source changes through V56/V68). **Live persistence remains unverified.**
- [x] **A04** Dashboard now offers Start Now and a Preview/Close Preview toggle, not an always-active ambiguous Stop. **Live interaction remains unverified.**
- [x] **A05** Keep renderer/watcher status on one bounded line rather than letting long messages force an excessively wide status card (V83); show full status as tooltip and allow text selection. **GTK sizing verification pending.**

## Preferences, configuration and controls (B)

- [x] **B01–B02** Adaptive navigation, titlebar and banner reachability at narrow widths (V79). **Physical narrow-window verification pending.**
- [x] **B03** Unambiguous save acknowledgment (`Saved.`) instead of guessing when watcher reload happens (V56, later state controller).
- [x] **B04** Single Save/Discard workflow in Preferences, no duplicate persistent header Save. **Live review pending.**
- [x] **B05** Non-reflowing unsaved-changes overlay styled for Adwaita. **Live polish review pending.**
- [x] **B06** Working font/color chooser, tab navigation and sticky dirty banner intentionally preserved, not treated as bugs.
- [x] **B201** Advanced Animation Timing defaults to collapsed and playlist controls use progressive disclosure (V75).
- [x] **B202** Slider values displayed above the slider thumb via Gtk.PositionType.TOP. **Visual check pending.**
- [x] **B203** Reset-to-factory affordances for animation timing values (defaults of 1 for multipliers); distinct from reverting unsaved state.
- [x] **B204** Reset-to-factory for target FPS, default 60, including monitor-specific FPS (current reset helpers).
- [x] **B205** Raw playlist JSON opens a separate editor window rather than expanding in the page.
- [x] **B206–B208** Per-monitor and shared auto-fit, and no fitting when auto-fit is disabled (V69). **Old crash near 52-pt fonts and mixed portrait/landscape setup must be confirmed on the real system, not declared resolved.**
- [x] **B209** Artwork chooser/editor and stored per-monitor artwork files (earlier releases and V78), rather than filename-only editing. **Live validation pending.**
- [x] **B210** Redesigned measured CPU/RAM/GPU/FPS display and layout (V76). **GTK visual review pending.**
- [x] **B211** Avoid repeated command logs in the dashboard. **Verify dashboard layout in live session.**
- [x] **B212** Dashboard distinguishes watcher process, automatic activation, and manual playback (V82). **Optional watcher-service start/stop control remains a proposal, not part of V82.**
- [x] **B213 (source)** Effect Library is now an application-owned, non-transient top-level window (V84). **KDE Task Manager visibility/grouping needs runtime confirmation.**
- [x] **B214** The single visible preview-mode selector lives in Effect Library (V81).

## Measurements, diagnostics and artwork editing (C)

- [x] **C01** Group measured effect durations by monitor/preview with meaningful units and summaries (V76). **Review live labels and selection.**
- [x] **C02** Artwork editor reports saved/closed/discarded separately and checks actual save outcomes (V78).
- [x] **C03** Diagnostics is its own readable window with PASS/FAIL, rerun/clear/copy, not raw output in General (V78).

## Effect Library and previews (D)

- [x] **D01** Clicking a preview thumbnail toggles selection; Play remains separate (V77).
- [x] **D02** Standalone preview centered, improved default size and resize handling via renderer anchor (V77). **Live resize behavior needs checking.**
- [x] **D03** Replay in independent preview window and removal of redundant Close button (V77).
- [x] **D04** Pinned preview made useful height instead of one clipped line (V77). **Live scroll and resize verification pending.**
- [x] **D05** Every effect card shows its qualitative length/intensity classification (V82).
- [x] **Responsive gallery UX** (V85, source): fixed Effect Library three-column minimum width replaced with adaptive 1–3-column FlowBox; both editors' filters stack on narrow windows, and empty search results have Clear filters without modifying selected effects. **Live GTK sizing and Save/Discard overlay verification pending.**

## Playlist Editor and order (E), main preview (F)

- [x] **E01** Consistent card selection/hover styling and removal of nested borders (V75). **Visual review pending.**
- [x] **E02 (source)** Playlist Editor no longer runs as an independently identified Wayland application; both editor windows use the installed ASCII Saver application ID (V84). **KWin grouping still needs a real-session test.**
- [x] **E03–E04** Gallery-first Playlist Editor, larger effect cards, search/filtering, collapsed metadata controls (V75). **Live window sizing review pending.**
- [x] **E05** Local Save/Discard in library and playlist editor; saving one form does not silently save/discard another (V74).
- [x] **F01** Redundant Help/preview text reduced in the library (V77).
- [x] **F02** Random effect selection and no immediate repeat at cycle boundaries; separate preview vs full-screen ordering (V68). **Live verification pending.**

## Artwork Studio development milestone (M1)

- [x] **V96 manual ASCII retouch (source):** 1-character ink brush/eraser at
  the text caret; mirror or flip selected text; bounded native Undo/Redo.
  Edits remain local to the buffer until explicit Save, never touch linked
  photo source or online provider. **GTK/Wayland validation remains open.**
- [x] **V97-V98 mouse canvas (source):** single-character paint/erase with
  interpolated drag strokes and shared Undo, then adjustable 75%-200% zoom,
  optional grid, scrolling viewport anchoring, responsive controls and Canvas
  keyboard Undo/Redo. Fractional scaling, pointer accuracy and GTK/Wayland
  usability remain unverified.
- [x] **V99 keyboard drawing and incremental buffer commits (source):**
  accessible arrow-key cell navigation, Space painting, Delete/Backspace
  erasing, visible cursor and scroll-to-cell, all sharing native Undo and
  explicit Save. Partial text-buffer replacements skip intermediate redraws,
  so unrelated text marks and drawing-cell position are better preserved.
  GTK keyboard/a11y, scrolling and Wayland scaling still require a live test.
- [ ] More elaborate brush sizes, rectangular selection and layers remain
  deferred until basic canvas drawing passes the live UX test.


- [x] **V94 custom glyph ramps:** 2–63 unique dark-to-light printable ASCII
  characters with implicit trailing whitespace, edited in Photo to ASCII
  Advanced. Same conversion, preview, preset and photo project; invalid
  settings clear stale previews and prevent export. Automated validation
  complete, desktop GTK/VTE testing outstanding.
- [ ] **M1 follow-up:** Real GTK/VTE keyboard, font-width and window-resize
  validation for custom ramps; full GNOME/KDE Artwork Studio workflow;
  optional ANSI color only with a verified safe representation.
- [ ] **M1 online verification:** Real remote connectivity and licensing
  still require validation. V92 ascii-bin provider is opt-in, source attribution
  retained, contributor-level rights remain unverified.

## Renderer and monitor reports (T)

- [x] **T01** Early startup cursor flashes mitigated with VTE/GTK cursor policy and overlay fixes through V66/V67. **Needs live GNOME/KDE confirmation.**
- [x] **T02** Keep final frame and avoid a visible caret after standalone preview ends (V73); requires real VTE confirmation.
- [ ] **T03** Full renderer testing on user's two differently oriented monitors is intentionally deferred until an agreed device-testing session.
- [x] Palette output authority covers built-in RGB effects; between-effect palette progression and palette-aware animated thumbnails (V70–V72). **Real RGB/VTE and multi-monitor test pending.**
- [x] Monitor hotplug controls and persistence for attached, detached and unsaved monitor configs (V80). **Live GNOME/KDE hotplug test pending.**
- [ ] GNOME fullscreen cursor handling and Dash to Dock layering after lock/unlock. Native clients cannot control GNOME Shell extension stacking. See [GNOME-VALIDATION.md](GNOME-VALIDATION.md) and [GNOME-DOCK-COMPAT.md](GNOME-DOCK-COMPAT.md).
- [ ] Watcher reported about **46 MiB RSS** in an older session. Not an actionable leak or private-memory measurement; only investigate after corroborating PSS/private usage.

## Deferred feature ideas, not approved for the next release

- [ ] More than one named, user-selected palette, transitions **between different palette collections**, curated themes, or extraction of 3-color palettes from images. The user explicitly postponed complex palette transitions.
- [ ] Safe KScreenLocker/wallpaper integration preserving authentication. This is a future milestone, not a finished screensaver replacement.
- [ ] Further adaptive navigation redesign with Adw.NavigationSplitView. Evaluate only after the existing design is tested.
- [ ] Expanding to additional non-KDE/GNOME compositors or unrelated desktop stacks. No user requirement to ship half-supported backends.
- [ ] Independent extra playlist automation styles, libraries, or large scheduling changes should be evaluated against actual confirmed user requests before coding.

## Newly approved future milestone: Artwork Studio / Photo to ASCII

The user specifically requested an intuitive built-in artwork editor that
progressively reveals advanced features; multiple creatively distinct templates
that inspire exploration; real-time previews side by side or stacked when narrow;
and eventually an online, searchable/filterable source of open-license ASCII
artworks. This **is approved milestone scope**, not an immediate obligation to
ship all items. See [ROADMAP.md](ROADMAP.md) for milestone phases and acceptance
criteria and [TASKS.md](TASKS.md) for the maintained checkboxes.

V86 starts with eight original editable creative templates and a searchable,
responsive preview picker inside the current text editor. Photo conversion and
online sources remain unchecked; no service or license is claimed integrated.

## Runtime validation queue (separate from source implementation)

- [ ] GNOME + KDE: Escape/pointer closes fullscreen; persistent preview remains open.
- [ ] Mixed portrait/landscape: auto-fit on/off/shared/independent; large fonts (~52 pt).
- [ ] Same/different palettes across monitors and effects; random/ordered sequence; round barrier.
- [ ] E02/B213 taskbar grouping and secondary-window visibility under KDE.
- [ ] V74–V85 UI, Save/Discard, live thumbnails, charts, editors and monitor hotplug; especially V85 small-screen FlowBox and breakpoint behavior.
- [ ] GNOME cursor and Dash to Dock stacking after lock/unlock.

## Design and release constraints

Use current checked [TASKS.md](TASKS.md) for concise next actions. Do not change an unchecked historical idea into an automatic feature. Keep `CHANGELOG.md` dated, plus a separate `RELEASE-Vxx.md` on every version. Do not claim a GTK/Wayland runtime fix on the basis of static tests alone.

## Artwork Studio V87 implementation update

- [x] Photo to ASCII basic conversion with original/ASCII responsive preview,
  crop/fit, three density styles, luminance adjustments and explicit local
  export; this is source-level checked, not live GNOME/KDE validation.
- [ ] Keep the milestone open: advanced controls, editable source/conversion
  metadata, asset browser/filtering, and licensed online sources are later
  phases. See ROADMAP.md for the canonical product milestone.

## Artwork Studio V88 implementation update

- [x] Progressive Advanced UI in Photo to ASCII: neutral-default gamma,
  local edge-definition and optional Floyd-Steinberg character dithering,
  with Restore defaults and shared debounced preview (headless source tests).
- [ ] Persistent editable photo-conversion recipes, local artwork
  browsing/filtering and vetted licensed online galleries remain future work.
- [ ] Live GTK/GNOME/KDE validation of the collapsed options, live preview,
  keyboard interaction and saved artwork re-opening.

## Artwork Studio V89 implementation update

- [x] Export an independently editable **photo project** alongside every new
  Photo to ASCII `.txt`: original image bytes, validated basic/advanced
  settings, versioned metadata and checksums. This is source tested only.
- [x] Reopen through the existing Artwork Editor, preserve manually edited
  text, and export new variants rather than overwriting previous assets.
- [ ] Verify the real GTK file-picker, conversion, resizing, reopen and all
  unsaved-changes cases on GNOME and KDE before marking runtime acceptance.
- [ ] Further image tools, offline local artwork catalog filtering, and
  properly licensed optional online providers are separate future tasks.

## Artwork Studio V90 implementation update

- [x] Offline local artwork gallery with real ASCII preview snippets, basic
  source/shape filters, search across names and user-written tags, and
  accessible Open Artwork and Clear Filters actions (headless tested).
- [x] Separate private and atomic per-asset tags, without writing inside the
  renderer's plain `.txt` format; invalid metadata cannot hide healthy assets.
- [x] Save a new personal copy from one of eight original creative templates
  with collision-safe filenames, without modifying current editor buffers.
- [ ] GNOME/KDE visual, small-window, keyboard, source/artwork and focus
  behavior remain unverified on a desktop. No claim of full milestone completion.
- [ ] Expand author/license provenance, animations/colors and online provider
  research in later phases; those filters are not falsely presented as live.

## Artwork Studio V91 implementation update

- [x] Six stylistically distinct built-in Photo to ASCII looks, applied through
  visible beginner-first controls and the existing responsive live comparison.
- [x] Collapsed personal preset manager for explicit named Save, Apply and
  confirmed Remove. Strict offline file validation, no overwrites, unchanged
  renderer `.txt` output and unchanged versioned photo projects (V89).
- [ ] Additional photo processing, creator/license metadata, and vetted online
  artwork sources remain separate future milestone tasks. Real GTK/Wayland
  testing remains necessary before confirming user experience.

## Artwork Studio V92 implementation update

- [x] Artwork Details in the local gallery now covers author, description,
  stated license, HTTPS source link and the existing tags. Metadata V1 read
  compatibility; V2 atomic sidecar writes. Artist/source values supplied by
  users are not independently verified; artwork `.txt` content is unchanged.
- [x] Initial read-only **ascii-bin** remote provider from its public text
  feed, with explicit fetch, search/tag/orientation filtering, real preview,
  per-item import confirmation, bounded offline cache and safe new local copy.
  The source repository claims CC0 on its compilation but disclaims being
  the creator of every individual work. Saved metadata never implies fully
  verified third-party rights.
- [ ] V92 real HTTPS fetch and GTK UI/keyboard tests on GNOME and KDE; the
  sandbox has no direct Internet or native GTK runtime. Other independently
  documented sources and remote publishing remain future milestones.

## Artwork Studio V93 implementation update

- [x] A posterization setting (2–8 luminance bands, or Off), plus selectable
  white/gray/black alpha matte for transparent photos, is implemented in the
  collapsed Photo to ASCII Advanced tools and uses the existing live preview.
  An RGB/opaque image remains unaffected by changing the alpha matte.
- [x] Projects and personal looks created in V89–V92 without the V93 settings
  load with neutral defaults. Newly saved recipes retain both settings.
- [ ] Confirm GTK/Wayland UI, keyboard access and visual output on live photos.
- [ ] More advanced blur/sharpen or edge-only artistic conversion remains a
  separately evaluated proposal, not a claimed V93 capability.

## V95 online discovery refinement (2026-11-08)

- [x] Approved M1.5 usability: browse ascii-bin's loaded collection in 48-art
  pages with Show More, measured size/title sorting and Surprise Me exploration.
  Filters do not modify original art, and an error on refresh leaves previously
  loaded entries accessible. The actual remote feed and GTK session are still
  pending end-to-end verification; see `ROADMAP.md` and `TASKS.md`.


## V97 artwork canvas follow-up (2026-11-08)

- [x] Native mouse-drawn character grid sharing Artwork Editor's unsaved GtkTextBuffer, explicit Save, brush/erase and one-stroke Undo. Source-level tests passed.
- [ ] Physically verify GTK drag, pointer accuracy at fractional scaling, scrolling, canvas/text transitions and Undo/Redo on GNOME/KDE before declaring M1 production-ready.
- [ ] Rectangular selection/layers are not implemented and are intentionally deferred until basic canvas UX is validated.

## V98 canvas viewport follow-up (2026-11-08)

- [x] V97 mouse canvas gains bounded zoom, non-destructive grid visibility,
  logical-cell hit testing and scroll anchoring, keyboard Undo/Redo and
  wrapping controls. The ASCII text and renderer format remain unchanged.
- [ ] Validate real GTK4 zoom, scroll restoration, pointer hit mapping under
  100%/125%/150% desktop scaling, keyboard focus and narrow-window layout.

## V100 Canvas work area and viewport follow-up (2026-11-08)

- [x] **V100 work area and visible-only redraw (source):** Canvas users can
  expand the editable grid without inserting filler text; painting/erasing
  still uses the same buffered explicit Save. The renderer's `.txt` model
  remains unchanged. Visible-only draw loops reduce off-screen Pango work.
  Model and simulated GTK callback tests are included. Live GTK/Wayland and
  Rust build remain separately unverified; do not conflate with closure of
  the Artwork Studio milestone.

## V99 Canvas keyboard and text-buffer follow-up (2026-11-08)

- [x] Source-level cursor navigation by arrows, paint/erase keys, location
  feedback in the existing hint and bounded scroll following the active cell.
- [x] Retain one Undo step per canvas edit but replace only a changed span;
  suppress redraw of the half-updated buffer and test the final state.
- [ ] Confirm focus delivery, keyboard navigation, GTK Undo, screen-reader
  announcements, and mouse/keyboard handoff on GNOME/KDE Wayland before
  claiming runtime completion. Defer extra tools until this is tested.


V103: Optional ping-pong palette progression (first → last → first) with existing per-monitor overrides and synchronized effect rounds. Desktop validation pending. See RELEASE-V103.md.
