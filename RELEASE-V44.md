# V44 installer hotfix

- Fix CMake project VERSION by providing a strictly numeric VERSION (`0.44.0`).
- Invoke `scripts/dependency-hint.sh` with Bash so missing executable bits do not mask errors.
- Do not reinstall system dependencies on arbitrary CMake configuration failures after dependency checks have passed.
- Bundled Rust build and KDE Wayland end-to-end operation remain unverified here.
