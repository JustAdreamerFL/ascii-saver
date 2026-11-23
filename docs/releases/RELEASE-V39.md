# V39: Uncapped simulation-hold reliability

Fixed an uncapped FPS busy-loop in the reference Rust renderer. With `--frame-rate 0`, `--simulation-hold` does not repaint an identical frame repeatedly. At positive FPS caps the configured repeat count is preserved. Added a Rust unit test.

**Status:** source change only. Rust compilation and KDE runtime checks are not possible in this environment.
