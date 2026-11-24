# ASCII Saver V113 (0.113.0) | package launcher fix

**Date:** 2026-11-24.

## Fix

Starting the screensaver or opening settings from a system package
installation could fail with:

```text
Could not start ASCII Saver: [Errno 2] No such file or directory:
/home/<user>/.local/bin/ascii-saver
```

The controller now resolves `ascii-saver` and `ascii-saver-settings` through
`PATH` when running from a package (`ASCII_SAVER_PACKAGE_DIR`), and selects the
matching packaged watcher (`ascii-saver-watcher-kde` or
`ascii-saver-watcher-gnome`). Development/user-local installations keep using
`~/.local/bin` and the private virtual environment.

## Validation

- New regression test covers packaged launcher, settings, watcher and ttfx paths.
- All 686 offline tests pass.
