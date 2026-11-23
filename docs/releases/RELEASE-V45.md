# V45: Fix Rust compilation failure during installation

## Fixed

- `ttfx-rust/src/engine/effect.rs`: remove the invalid outer `1..` in the
  simulation-hold paint loop. `repeat_count()` already returns
  `std::ops::Range<u32>`, and nesting it in another range triggers Rust
  `E0308` (expected integer, found `Range<u32>`).
- Add an offline regression guard that checks this specific source contract.
- Update the numeric CMake-compatible application version to `0.45.0`.

## Known limitations

- The user's CachyOS log confirms the watcher C++ target builds successfully;
  this environment cannot run Rust's Cargo toolchain, so the patched Rust
  binary has **not** been compiled here. Another compiler error may surface
  after this one is resolved.
- KDE Wayland and the GUI have not been runtime-tested here.

## Recommended validation on CachyOS

```bash
./install.sh
./verify-build.sh
```

`verify-build.sh` runs all Python and Rust tests, the release compilation,
then the renderer smoke test. The installer stages the new binary and retains
an existing installation if the Rust build fails.
