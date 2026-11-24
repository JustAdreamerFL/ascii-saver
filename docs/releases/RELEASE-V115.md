# ASCII Saver V115 (0.115.0) | idle watcher toggle

**Date:** 2026-11-24.

## Changes

- Preferences now includes an **Idle watcher** switch in the Activation group.
  Turning it on starts the watcher immediately and enables it for later logins;
  turning it off stops the watcher and writes a per-user autostart mask.
- Package installations are detected as using XDG autostart. Diagnosis no
  longer reports only a stale, disabled systemd user unit when the packaged
  watcher is configured or running.
- Enabling the packaged watcher disables any leftover `ascii-saver.service`
  from an earlier development installation so it cannot launch a deleted
  `~/.local/bin` executable.

## Validation

- New unit tests cover autostart masking, re-enabling and watcher state.
- Preferences was opened under a virtual X display from a package layout.
- All 690 offline tests pass.
