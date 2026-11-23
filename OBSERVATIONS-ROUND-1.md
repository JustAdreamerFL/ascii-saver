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
