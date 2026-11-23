# ASCII Saver V73 (0.73.0): stable effect preview completion

## Changes

The standalone **Effect Preview** and the embedded Effect Library preview now
launch the bundled Rust renderer with `--no-color --no-eol --no-restore-cursor`.
V72 had omitted `--no-eol` in both modes, and the embedded preview also omitted
`--no-restore-cursor`. The Rust engine sends a trailing newline unless
`--no-eol` is specified, even when cursor restoration is disabled. Therefore
those modes could move/scroll the last painted frame and show the VTE caret
when the renderer finished. The fullscreen/persistent renderer already used
these flags; its behavior is unchanged.

The embedded preview now emits VTE's hide-insertion-cursor sequence before
its child starts and again after child exit. The standalone preview already
had those cursor feeds. Neither completion callback redraws or clears its
terminal; the last frame remains in VTE as-is.

Additionally, a failed deletion of a temporary frame-statistics report no
longer prevents the fullscreen child-exit callback from proceeding to the
per-monitor hold/synchronization barrier. The error is logged and playback
continues.

## Verification

GTK-free automated tests exercise the real fullscreen child-exit callback with
a simulated permission error. AST tests confirm the actual VTE spawn argument
lists and cursor behavior in both preview modes. Full Python suite, installer
checks, release assets, and syntax verification are required before packaging.

**Limits:** The Rust binary has not been compiled in this environment because
Cargo is unavailable. The real GTK/VTE + Wayland behavior remains untested.
This is a cumulative development build; user-side testing is still deferred.
