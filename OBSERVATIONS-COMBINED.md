# KDE ASCII Saver — Consolidated testing feedback

Compiled from the user’s V53 hands-on testing. Some observations are addressed by V54; others remain open. For exact V54 status, read RELEASE-V54.md and UX-ROADMAP.md.

---
## Round 1

# KDE ASCII Saver V53 — User testing observations

**Round:** 1 (initial feedback, 2026-10-18)
**Source:** User's first extended live-test report after installing V53.
**Status:** Round 1 captured; user authorized work on next version after Round 2 on 2026-10-18.
**Evidence level:** User-observed behavior, not yet independently reproduced or diagnosed. Statements of desired behavior are recorded as requests, not as implemented features.

## Observations and requirements

### A. Application identity, runtime, and the main window

**A01 · Application naming**
- Current spoken/visible name ("KDE ASCII Saver", sometimes abbreviated to "KDE AC saver" / "KDE RC saver" in dictation) doesn't communicate the application's purpose naturally.
- Consider a shorter, more accurate name such as **KDE AC**; "KDE terminal effect screensaver" is descriptive but too long.
- This is a naming suggestion, **not a finalized choice**.

**A02 · Excessive idle CPU consumption (high priority)**
- Merely opening the V53 main UI/preferences, with no screensaver or effect intentionally rendering, consistently uses roughly **8–8.2% total CPU** in htop, described as one CPU core running at full utilization.
- Opening a preview window does not seem to change that utilization noticeably.
- Investigate the actual process/thread and cause; avoid treating the observation as proven to be the renderer, GTK, the idle watcher, or an animation timer before profiling.

**A03 · Main Preview action closes on activity**
- The main-window **Preview** closes/hides when a key is pressed or the pointer moves.
- User expects an ordinary **persistent, resizable preview window**, not an idle/screensaver-style view that exits on input.
- It should preview the **real playback sequence**: first effect, subsequent effects, playlist/order behavior, potentially cycling over time. Differentiate this from **Start Now** (real screensaver, which should exit on activity).

**A04 · Stop button purpose/state unclear**
- **Stop** appears clickable when no animation is running, and the user cannot tell what it stops.
- Clarify its scope (screensaver vs preview vs rendering session) and enable/disable it according to that session's actual state, or redesign/remove if redundant.

**A05 · Main dashboard activity/status layout breaks at narrow widths**
- At minimum main-window width, the status line containing phrases like "renderer stopped" and "idle watcher running" wraps from two lines to three and distorts the status card height/layout.
- Responsive design should avoid awkward wrapping and shifting/card stretching.

### B. Responsive preferences and feedback

**B01 · Preferences header is not properly responsive**
- Narrow, tall Preferences window can hide titlebar/window controls (close, minimize, maximize) and the Save button.
- Main window handles minimal width better.

**B02 · Bottom category navigation gets clipped**
- At small widths, final category tab is completely inaccessible and second-to-last is partially clipped.
- Every category must remain accessible at supported window sizes, using a true adaptive navigation solution.

**B03 · Preferences saved toast is ambiguous**
- Message: "Preferences saved. Idle watcher will reload them automatically."
- It does not explain **when** settings become active (immediately, next idle cycle, after relogin, etc.).
- Use short, precise feedback grounded in actual reload semantics.

**B04 · Duplicate Save controls**
- Persistent Save button in window header duplicates the floating unsaved-changes banner's **Save** and **Discard** actions.
- Consolidate to one comprehensible workflow, without redundant affordances.

**B05 · Unsaved-changes banner doesn't look native**
- Floating banner is useful and remains visible across tab changes, but its styling doesn't feel like real libadwaita.
- Preserve its **non-layout-shifting** behavior; use a native-looking/appropriate Adwaita approach for a persistent dirty-state action.

**B06 · Settings that are working**
- Preferences category pages are navigable/responsive in ordinary layouts.
- Color pickers and font picker work.
- Save/Discard toasts appear; floating dirty banner persists when moving between categories (desired).

### C. Per-effect durations, diagnostics, and artwork editing

**C01 · Measured effect durations should be grouped and styled**
- Per-effect duration logging now works (positive).
- Current view is an unstructured/raw-looking list/table: effects from DisplayPort 1 run directly into DisplayPort 2, then into a Preview group without clear headers.
- Provide a real libadwaita-styled structured page with distinct groups, readable display names, and a selector/filter to switch between monitors and preview or see all.
- Avoid identifying displays only as DisplayPort 1 / 2 when meaningful monitor names are available.

**C02 · Artwork editor completion message fires prematurely**
- Clicking **Edit Artwork** reports an edit started, then an "edit completed" toast even while the external editor remains open.
- Completion should wait until the editor **closes** and any changes are **saved to disk**; distinguish "Closed without changes" from "Artwork saved".
- Differentiate artwork-edit feedback from configuration-change feedback.
- The existing "Editing edit" wording also sounds odd.

**C03 · Diagnostics output appended to General**
- **Run Diagnostics** appends a wall of diagnostic text directly inside the General preferences page, with no explicit Clear action.
- Closing Preferences happens to clear the output; that behavior is okay but not a good presentation.
- Prefer a purpose-built results dialog/page with actions such as close/clear/copy, keeping General uncluttered.

### D. Effect Library cards, playback, and filtering

**D01 · Clicking the artwork thumbnail should toggle selection**
- In Effect Library the card's image/artwork area does **not** toggle the effect's enabled state.
- Match Playlist Editor interaction, where clicking the artwork does toggle it. Keep **Play** a separate explicit action.

**D02 · Standalone single-effect preview is poorly laid out**
- From library **Play**, the preview appears in a relatively small window with the artwork anchored to the **upper-left** instead of visually centered.
- The artwork should be centered, and the window/canvas should fit its content predictably.
- Resizing during playback produces distorted/weird framing. Either make the preview resize correctly, or use a deliberate fixed content-driven size/constraints.
- Too much descriptive text in the preview (e.g., "previewing [effect] … artwork", "independent preview, mouse move …") is unnecessary and should be simplified.

**D03 · Preview controls need cleanup**
- When a single-effect preview finishes, there is no obvious **Replay** action *inside that preview window*.
- A separate **Close preview** button duplicates the window manager's close button; remove redundant controls.
- Existing **Replay last effect** in the library is a positive feature and may remain.

**D04 · Embedded preview unusably shallow**
- Pinned/below-cards preview is only about **one line high**, not resizable, and clips the artwork.
- Give embedded preview adequate height and/or resize affordance, while preserving the card gallery and scroll behavior.

**D05 · Display effect classifications on each card**
- Filtering by duration and intensity works (positive).
- Show each effect's classification on its card: **short / medium / long** and **gentle / moderate / energetic**, so users know why a filter includes it.

### E. Playlist editor functionality and layout

**E01 · Playlist card nested hover outlines / mismatched components**
- Hovering the artwork highlights an inner bounding box on top of the enclosing card, resulting in a visually doubled card.
- Playlist Editor and Effect Library should share one consistent card component and selection/play interactions.
- Clicking the playlist card's artwork already toggles selection correctly (positive).

**E02 · Playlist editor taskbar/app identity inconsistent**
- Playlist Editor shows in KDE Task Manager as a **separate process/window with a generic Wayland icon**, not grouped under the KDE ASCII Saver app icon.
- Effect Library appears in KWin Overview with the app icon, but is **not visible in Task Manager** under the main app's windows; hovering the main app only shows Main and Preferences.
- Ensure correct app IDs, icon assignment, window role/type, grouping, and sensible taskbar visibility across secondary windows. This may involve app identity and transient-parent settings; root cause unverified.

**E03 · Sidebar and editor look like unstyled GTK**
- Playlist sidebar items, playlist order list, and main content have inadequate padding/margins.
- "Playlist order (top to bottom)" starts at the left edge; visual hierarchy feels like a mix of unrelated GTK and Adwaita components.
- Rebuild using coherent, native Adwaita groups, rows, spacing, and layout.

**E04 · Playlist editor layout wastes most of the window**
- Opening Playlist Editor unexpectedly goes straight to a **Playlist Details** view.
- Automatic Playlist and Current Playlist sections consume much of the vertical space; the effect cards and their previews are confined to a tiny region.
- Resizing doesn't effectively recover useful space. Prioritize the visual effect gallery, selection, and ordering instead of bulky meta sections.
- User considers a **from-the-ground-up playlist editor redesign** necessary.

**E05 · Save/Discard feedback must belong to the window being edited**
- Toggling an effect in Effect Library shows the unsaved banner in the **Preferences window**, not in the library itself.
- Changing playlist settings only presents a **Save Playlist** button, with no equivalent dirty-state / Discard behavior.
- Need a consistent model across Prefs, Library, and Playlist Editor: show Save/Discard contextually **in the active window** and make the scope/meaning of each save clear.

### F. Preview Help, playback order, and behavioral semantics

**F01 · Preview Help lacks useful content**
- The Help section for Preview looks sparse, possibly not useful. Improve concrete guidance or remove/merge it into relevant controls.

**F02 · Random effects aren't actually varying**
- With **Use ordered playlists** disabled, starts seem to play the **same first effect and same effect sequence** each time.
- Tooltip promises random effect selection when ordered playlists are off.
- Make that behavior genuinely random across starts, ideally avoid immediate repeat patterns, and verify against the configured options.

## Desired direction / constraints carried forward

- The user has now authorized work on V54 after Round 2; UX first, then renderer functionality.
- Treat user's live test on **CachyOS / KDE Plasma Wayland, two DisplayPort-connected monitors** as the primary behavioral report.
- Preserve the good parts: adaptive category navigation in normal-size windows, floating banner that does not move page content, working color/font pickers, measured per-effect timing, search/filter, Replay last effect, clickable playlist thumbnails.
- Distinguish two different types of preview: **main real-playlist preview** (persistent, resizable, continuous sequence) vs **single-effect library/editor preview** (deliberate replay, centered and sensibly sized); neither should be mistaken for the activity-dismissed fullscreen screensaver.
- Do not assume any suspected root cause is confirmed until source/runtime investigation.

## Pending

- Round 2 of user observations: awaiting input.
- Work authorization: **given** after Round 2, on 2026-10-18.

---
## Round 2

# KDE ASCII Saver V53 — User testing observations, Round 2

**Date:** 2026-10-18. **Scope:** UX and responsiveness first. User has now explicitly authorized work on the next version.
**Evidence:** User's firsthand runtime report on CachyOS, KDE Plasma 6 Wayland, one landscape and one portrait monitor. Not independently reproduced here.

## Preferences: numeric controls and reset semantics
- **B201** Advanced Animation Timing being collapsed by default is good and should be retained; apply analogous progressive disclosure to playlist controls.
- **B202** Slider current-value labels should appear above the slider thumb rather than permanently to its right. Min/max should remain understandable.
- **B203** Every timing slider should expose a Reset to factory default button only while away from factory value. All timing multipliers default to 1: output pacing, frame dwell, elapsed-time speed, simulation hold. Distinguish reset-to-factory from reverting *unsaved* changes.
- **B204** Apply the same reset affordance to other configurable values such as target FPS (default 60), where practical. Persist factory defaults separately from saved values so resetting is always available after settings have been saved.
- **B205** Raw playlist JSON should open in a real separate editor, not an awkward expanding text field embedded in the preferences page.

## Display and artwork behavior
- **B206** Auto-fit artwork does not appear truly independent: font is reduced according to the narrower monitor and shared across both monitors even when independent settings are enabled.
- **B207** Switching Auto-fit off still seems to retain the reduced font. Off must mean no automatic resizing; reopening preview should use configured font again.
- **B208** When independent monitor settings are off, artwork size unexpectedly shrinks on both displays and preview can hang. Joint-mode behavior must be specified clearly and tested.
- **B209** Monitor-specific artwork should be selected with a file chooser/library, not a text filename. Use a dedicated on-disk config artwork directory, preserve external scripting/programmatic modifications; do not embed user artwork inside application code.

## Screens, status and navigation
- **B210** Performance graphs window remains scattered; graphs and numerical units need legible scale, group spacing and appropriate native Adwaita page construction. A tiny scrollable embedded preview is not useful.
- **B211** Main window appends persistent output such as “Started KDE ASCII Saver” at the bottom; don't show redundant command logs inline when the controls already indicate the action.
- **B212** Clarify start/stop controls: consider a clear Start/Stop Idle Watcher action instead of a Stop button that's active when no renderer is running.
- **B213** Effect Library window is oddly always above Preferences and absent from grouped KDE taskbar window list. Review transient parent, modal/utility hints and app identity.
- **B214** The Preview Behavior selector is actually an Effect Library option. Move it to the library where it is used, or clearly label its scope (applies to effect library, not playlist/main preview).

## Animation engine observations, parked separately
- **T01** On starting screensaver, a terminal block/caret flashes in the top-left just before the effect draws. During animation it is absent.
- **T02** In standalone preview, the caret appears at the bottom after an effect finishes, rather than keeping the finished artwork without a cursor.
- **T03** User will perform deeper runtime/rendering behavior tests *after* UI usability round. UI first; cursor issue may be addressed early if isolated.

## Positive feedback to preserve
- Advanced timing is initially collapsed. Existing previews and font/color selection remain useful. Per-effect duration logging and search filters from Round 1 are functional; don't regress them.

---
## Separate renderer backlog

# KDE ASCII Saver — terminal effects / renderer backlog

These issues are separate from V53 UI usability work. Fix UI first, then test render behavior. They are observed on a KDE Plasma Wayland setup with two differently oriented monitors.

1. **Cursor flash at startup:** a terminal caret/block flashes in the upper-left before the first frame of a fullscreen screensaver effect (T01).
2. **Cursor visible after preview effect ends:** VTE displays a caret at the bottom after rendering finishes in a standalone preview; no caret during actual animation (T02). Renderer should keep final frame and hide text cursor before, during, and after animations.
3. **Per-monitor artwork scaling:** auto-fit should respect the configured independent/shared mode and NEVER fit if disabled. Test portrait vs landscape monitors and the first frame, after effects complete, and after preferences changes.
4. **Actual random playback:** with ordered playlists disabled, sequence/first effect appeared identical each start (Round 1 F02); verify seeding and scheduling behavior.
5. **Palette progression and final ANSI colors:** preserve effect-generated color in held final frame; verify interpolated palette transitions *between* effects, not during an effect.
6. **Persistent playlist preview:** distinguish persistent, resizable playlist preview from real screensaver exit-on-input (Round 1 A03).

Status: observations collected; runtime root causes not proven. UI priority first, renderer work later unless small isolated fixes can be verified.
