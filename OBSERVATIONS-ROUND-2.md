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
