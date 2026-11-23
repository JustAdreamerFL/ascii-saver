# V27 Rust ttfx instrumentation (experimental)

This source archive contains the updated KDE application and a patched Rust ttfx source tree in `ttfx-rust/`.

Build with Rust toolchain:

```sh
cd ttfx-rust
cargo build --release --locked
cd ..
KDE_ASCII_SAVER_TTFX="$PWD/ttfx-rust/target/release/ttfx" bash install.sh
```

The unmodified ttfx executable does not recognize `--stats-file`. You must build this bundled Rust source to use V27.

Each effect logs `frame_stats` including output frame count and measured average output FPS. These are frames emitted by ttfx, not display-presented FPS.

Validation: Python syntax passed; Rust compiler unavailable in this environment, so Rust compilation and Plasma runtime are unverified.
