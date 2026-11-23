# V33 source-check release

- Fixes `--virtual-clock --time-scale` so simulation time advances by `time_scale / frame_rate` each output frame.
- Preserves original virtual timing for `--parity-dump`, so parity test fixtures are unchanged.
- Adds two Rust regression tests, plus `./verify-build.sh` for actual Cargo tests and release build.
- Does not implement universal duration scaling for all frame-step effects.
- Cargo is unavailable in the packaging environment; the Rust source remains **uncompiled and unverified**.
- This archive is experimental and **not** a verified installation release.
