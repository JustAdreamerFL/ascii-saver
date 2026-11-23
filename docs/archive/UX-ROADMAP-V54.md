# UI follow-up priorities after V54

This is a historical V54 issue list, not a claim of resolved bugs. For current checked status and priorities, see [TASKS.md](../../TASKS.md).

## Next highest-priority UX work
1. Rebuild Playlist Editor around full-height effect thumbnails and accessible selection / ordering; keep auto-playlist controls collapsed, secondary.
2. Give Effect Library and Playlist Editor their own Save/Discard state at the edit location. Shared preferences state must remain synchronized without hidden writes.
3. Fix KDE Wayland secondary-window identity/grouping, including library hidden from taskbar and playlist separate process.
4. Rebuild performance history with correct units/scales and clear distinction between per-monitor child processes and the shared GTK/VTE process.
5. Improve single-effect preview positioning, replay/close UX, in-window controls, and pinned preview sizing.
6. Move Effect Library preview mode choice into its own window, and remove confusing or redundant Help.
7. Present diagnostics as a standalone results window; delay artwork edit completion messages until external editor closure and saved file verification.
8. Add start/stop monitoring controls for the idle watcher with clear status and conditions. Determine real CPU use via collected process/thread evidence.
9. Inspect taskbar grouping plus responsive preference width/height on actual Wayland session.

## Later renderer behavior
See RENDERER-BACKLOG.md, especially cursor state, palette effects, random order, multi-monitor fitting runtime and final artwork preservation. The user requested prioritizing UI until the interface is usable.

## GNOME session observations, November 2026

- [x] Detect 1 versus multiple displays in dashboard labels via `GdkDisplay` `items-changed`, without polling.
- [x] Update display-count explanation in Preferences via the same signal.
- [x] Dynamically rebuild per-display FPS, artwork and palette controls when displays are hot-plugged/unplugged; preserve unsaved values and settings of disconnected monitors. (V80 source patched; live Wayland verification pending.)
- [ ] Confirm fullscreen pointer stays hidden on GNOME Wayland after the V61 on-map GDK surface cursor fix.
- [ ] Verify Dash to Dock / GNOME Shell visual stacking after lock/unlock. Normal Wayland clients do not control the order of GNOME Shell actors; potential optional Shell extension integration should be designed separately and never forcibly modify another extension.

## Proposed (not implemented in V63)

- Evaluate `Adw.Sidebar` / `Adw.NavigationSplitView` for Preferences on wider windows with adaptive stacked navigation on narrow screens. Do not switch layouts until usability and KDE Wayland behavior can be tested.
- GNOME pointer still appears over fullscreen in V62: first verify current running GUI/watcher and whether the pointer is GTK surface-local or GNOME Shell-controlled; verify Dash to Dock independently.
