# ASCII Saver V103 (0.103.0)

## Added
- Optional **Reverse palette at the ends** toggle in Appearance. For palettes of 3+ colors, effect rounds traverse forward and then backward, avoiding the abrupt last-to-first jump.
- Existing palette interpolation still uses Effects per color transition, and the color changes between effects rather than during an effect.
- Existing per-monitor overrides, shared synchronized rounds, and independent preview palette clock are preserved.

## Compatibility
- The new `palette_ping_pong` configuration key defaults to false, so old palettes retain their prior order. Invalid non-boolean values fall back to false.
- No new renderer dependencies or color formats.

## Verification
- Headless Python tests and installer checks are run for this release. No live GTK/KDE/GNOME desktop verification, Rust build or actual monitor hardware tests.

## Open
- Multi-monitor synchronization, watcher inhibition, actual palette appearance and performance need runtime testing.
