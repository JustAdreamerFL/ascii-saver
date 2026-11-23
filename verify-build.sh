#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 scripts/check-release-assets.py
python3 -m unittest discover -s tests -q
bash tests/test_installers.sh
if ! command -v cargo >/dev/null 2>&1; then
  echo 'ERROR: Cargo is required to verify the Rust source.' >&2
  echo 'Install rustup/cargo, then run ./verify-build.sh again.' >&2
  exit 127
fi
cargo test --manifest-path ttfx-rust/Cargo.toml --locked
cargo build --manifest-path ttfx-rust/Cargo.toml --release --locked
python3 scripts/smoke-renderer.py ttfx-rust/target/release/ttfx
python3 -m compileall -q .
bash -n install.sh
bash -n uninstall.sh
printf 'Rust build and available source checks passed. KDE Wayland remains untested.\n'
