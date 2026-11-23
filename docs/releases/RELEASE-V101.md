# ASCII Saver V101 (0.101.0)

Date: 2026-11-08. **Experimental cumulative source release.**

## Core playback reliability: start, preview and stop

This release deliberately shifts work away from the Artwork Studio milestone and
back toward the **main screensaver lifecycle and dashboard**.

- **Accurate start mode:** `ascii-saverctl preview` no longer reports success
  when the fullscreen renderer is already running, and `start` no longer
  reports fullscreen success for an existing windowed preview. A conflicting
  request fails with a clear Stop-first message **without touching the running
  session**. Repeating a command in its already active mode is idempotent.
- **Verified stop:** `ascii-saverctl stop` still sends an identity-checked
  SIGTERM only to the installed renderer, but now waits up to 2.5 seconds to
  confirm that PID is no longer the renderer. It reports success only after
  confirmation. If it does not exit, the command returns failure, suggests
  checking status/logs and **does not force-kill** the process. Already-exited
  instances and permission errors are handled distinctly.
- **Status clarity:** The GTK dashboard now says **Preview running** or
  **Fullscreen running**, instead of merely Running. `ascii-saverctl status`
  also prints the current playback mode. Automatic idle activation and
  watcher-process status remain separate from manual playback.
- **Serialized dashboard commands:** Start Now and Preview/Close Preview cannot
  overlap. A two-second status refresh cannot inadvertently re-enable one
  control while the other is still running. Controls recover on command
  completion and closed GTK windows are not updated afterwards.
- **Bounded dashboard execution:** The new GTK-free `dashboard_playback.py`
  runs the CLI with a 10-second timeout; nonzero exits and timeouts display
  failure text rather than a misleading success toast. `settings.py` stays
  below its existing modularity size guard. The installer includes the helper.

## Verification

- Added `tests/test_v101_playback_lifecycle.py` covering start-mode conflicts,
  idempotent requests, exit polling, stop timeouts, identity-checked SIGTERM,
  permission failures, status labels and dashboard execution.
- Full Python suite, installer, session detection and syntax checks run on the
  source tree. The cumulative ZIP is integrity-checked after creation.
- **Not verified on a live desktop:** Actual KDE/GNOME native GTK interaction,
  externally started renderer races, stop under a wedged renderer, or
  full-screen multi-monitor behavior. V101 does not rebuild the Qt watcher
  or Rust renderer, and does not modify effect scheduling.

## Next whole-application priorities

1. Live KDE/GNOME validation of Start/Preview/Stop, taskbar identity and monitor hotplug.
2. Watcher/renderer inhibition and crash recovery with concrete evidence.
3. Multi-monitor sync and responsiveness under active playback, without
   claiming that a source-level test substitutes for a physical session.
4. Artwork Studio remains an ongoing milestone, but not the only workstream.
