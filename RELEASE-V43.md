# V43: Offline verification and dependency-aware integration tests

- The GTK-dependent screen-lock lifecycle test now skips cleanly when PyGObject is absent, while still running on GTK-capable hosts.
- Added offline checks for the complete 37-effect GIF library: unique IDs, nonempty and valid GIF headers, installer staging and GUI lookup paths.
- `verify-build.sh` now runs pure-Python tests, release asset validation and installer tests before attempting Cargo.
- Rust compilation and KDE Wayland functionality are **not** verified by these offline checks.
- Updated installer integration tests for the Rust `ttfx` binary and the `tte -> ttfx` compatibility link, using a stub binary exposing the required options.
- Fixed executable permissions of installation entry points in the distributable archive.
- Note: installer tests use a mock renderer and do not replace Cargo compilation.
