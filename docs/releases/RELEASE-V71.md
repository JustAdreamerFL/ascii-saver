# ASCII Saver V71 (0.71.0): one authoritative palette

## Changes

- Fullscreen effects always use the selected shared palette or their per-display override. The built-in Rust renderer now runs with `--no-color`, so effects that produce ANSI foreground or background RGB gradients cannot override the chosen VTE foreground.
- Normal fullscreen selection, shared effect synchronization, palette cycling between effects, and independent monitor palette selection remain unchanged.
- Persistent playlist preview follows the same restriction. Both live preview modes in the effect library use the currently selected color swatches and background, including unsaved edits, while preserving their independent window lifecycle.
- There are **no new palette-transition controls**. Only the existing between-effect color progression remains.

## Behavior tradeoff

The strict setting makes each effect **monochromatic in the current palette color**. For effects whose internal per-character RGB gradients convey depth or shading, those gradients will no longer appear; characters and animation timing are preserved. The chosen background still applies. This avoids blending or displaying arbitrary effect-generated RGB outside the selected palette. Effect art used in *static thumbnails* is a separate image asset and is not recolored by this change.

## Verification

- New GTK-free Python tests exercise the actual palette-application helper and confirm each of the three live `ttfx` launch paths passes `--no-color`, including both effect-library modes.
- The `--no-color` Rust VisualPool formatting path was inspected; it suppresses 24-bit/XTerm foreground and background SGR formatting and is plumbed through the Rust CLI and engine.
- The Rust toolchain and a Wayland GTK/VTE desktop are not installed in this environment, so a compiled Rust smoke run and live visual validation are deferred. Run the installer on a test machine before deployment.
