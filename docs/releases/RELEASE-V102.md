# ASCII Saver V102 (0.102.0)

Date: 2026-11-08. **Experimental cumulative source release.**

## Core watcher reliability (not Artwork Studio)

### 1. KDE: do not start a second screensaver over a manual one

- The Qt/KIdleTime watcher previously checked only its own `QProcess`, unlike
  GNOME's existing manual-renderer check. A manually launched Preview or
  fullscreen renderer could therefore be followed by an unnecessary competing
  idle launch.
- At both the first KIdleTime callback and `startSaver`, the KDE watcher now
  validates the application's shared runtime PID file and exact Python
  `app.py` process identity. When a manual renderer is running, leave it
  untouched and keep the automatic request deferred. The deferred recheck
  waits for that renderer to exit and for activity inhibitors to clear;
  any user resume cancels the pending request.
- This change is limited to automatic idle activation. It does not take over,
  terminate or change an existing manual Preview or fullscreen session, and
  it does not modify multi-monitor effect scheduling.

### 2. GNOME: recover from stale native-watcher PID files

- Previously GNOME's PID claim refused to start if the old PID was running,
  even when the kernel had reused that PID for an unrelated process.
- The new native watcher claims and holds an exclusive nonblocking advisory
  `flock` on its own runtime PID inode for the process lifetime. It verifies
  whether a pre-existing PID identifies a genuine legacy watcher before
  replacing it, so a still-running old service is not ignored.
- At exit, only the same locked inode containing its own PID is removed.
  Symlink paths are rejected; ownership and regular-file checks are enforced.
- GNOME's existing check for an active manual renderer now uses the common
  exact-script identity helper rather than its own `cmdline` parser.

### 3. Shared Linux process identity helper

`watcher_process_identity.h` is pure Linux POSIX C and C++ with no GUI
imports. PID read is bounded (64 bytes), accepts a decimal PID only from a
regular non-symlink file, and identifies a renderer only when the same-user
`/proc/PID/cmdline` has the exact expected absolute script path as `argv[1]`.
The native watcher identity compares `/proc/PID/exe` to the current
executable, allowing the old executable's ` (deleted)` suffix during upgrades.

## Verification and constraints

- Added `tests/test_v102_watcher_ownership.py` and a native probe that is
  compiled under `cc` and `g++` with `-Wall -Wextra -Werror`. Tests spawn real
  short-lived Python renderer processes and check valid, malformed, symlinked,
  oversized and unrelated PID cases, argument-position identity, old watcher
  executable identity and integration source contracts.
- Full Python test suite, install/session scripts, Python syntax check and
  ZIP integrity are part of source verification.
- **Not validated:** Native Qt6/KF6IdleTime build or GNOME/GIO/JSON-GLib
  build, neither of which has development dependencies in the current
  environment; actual KWin/Mutter D-Bus notifications, idle timing, inhibitor
  behavior, service shutdown and mixed-monitor sessions need a live system.
- Rust/TTE renderer, multi-monitor scheduling, and Artwork Studio are left
  unchanged by V102. V101 dashboard controls remain present.

## Next core priorities

1. Actual native watcher rebuilds and KDE/GNOME idle/manual conflict tests.
2. Monitor synchronization, hotplug and inhibitor handling under real load.
3. Watcher responsiveness/idle cost measurements and failure recovery.
