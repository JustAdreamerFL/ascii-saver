# ASCII Saver V111 (0.111.0) | native packages

**Date:** 2026-11-23. Experimental source and package release.

## Packages

- **Debian/Ubuntu:** `ascii-saver_0.111.0_amd64.deb`
- **Fedora:** `ascii-saver-0.111.0-1.fc43.x86_64.rpm`
- **Arch Linux:** `ascii-saver-0.111.0-1-x86_64.pkg.tar.zst`

The packages install under `/usr`, use the distribution Python/GTK runtime,
and include prebuilt GNOME and KDE idle watchers plus the instrumented `ttfx`
renderer. No virtual environment, compiler, or Cargo toolchain is needed on
the installed machine.

Desktop integration is installed system-wide: application entry and icon,
AppStream metadata, systemd/XDG autostart, the optional KWin fullscreen script
and the optional GNOME cursor bridge. Uninstalling through the package manager
removes these files while leaving `~/.config/ascii-saver` user data intact.

## Release automation

The manual **Release** workflow now builds source archives, Debian/RPM/Arch
packages, per-archive checksums and a combined `SHA256SUMS`, then attaches all
of them to the GitHub release. The workflow refuses tags that do not match
`VERSION` or already exist.

## Validation

- All 683 offline tests pass.
- Debian 13, Fedora 43 and Arch packages were built and installed in container
  smoke tests; `ascii-saver --version` and `ascii-saverctl components` run from
  the packaged layout.
- `tests/test_packaging.py` enforces version and package-definition parity.
