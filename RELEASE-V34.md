# V34: instrumented Rust build integration

The installer now builds the bundled Rust renderer with `cargo build --release --locked` automatically, or uses an explicitly specified `KDE_ASCII_SAVER_TTFX` binary after checking its CLI capabilities. It no longer silently selects a potentially incompatible system `ttfx`. Rust compilation occurs in a temporary transaction directory before installing the application files. A failed build stops installation without replacing the existing installed app. Requires Cargo and network access to any crates not cached locally.

Verification: shell syntax and source-level installation-contract tests run; Rust compiler and real Plasma Wayland runtime are unavailable in this environment. No claim of successful Rust compilation.
