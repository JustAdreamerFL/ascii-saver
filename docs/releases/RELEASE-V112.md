# ASCII Saver V112 (0.112.0) | package-manager installs

**Date:** 2026-11-24. Experimental source and package release.

## Installer

`install-online.sh` is now the user-mode installer. It detects the
distribution, release and architecture, downloads the matching package from
the GitHub release, verifies it against `SHA256SUMS`, and installs it with
`apt`, `dnf` or `pacman`. No virtual environment, Python, or Cargo is required
on the installed system. The previous user-local build remains available with
`--source`.

Supported native targets:

- Debian 13 and Ubuntu 26.04+
- Fedora current and previous releases (Fedora 45 and 44 for this release)
- Arch Linux and derivatives (rolling)

## Release automation

The manual **Release** workflow now resolves the current Fedora release from
`fedora:latest`, builds that release plus the previous one, and builds Debian
and Arch from their latest rolling/stable images. It publishes source archives,
all packages and a combined `SHA256SUMS`.

Release notes are generated from the uploaded files: newest Debian, Fedora and
Arch packages appear in the main table, older Fedora builds in an expandable
section, with separate expandable source and checksum sections.

## Validation

- All 685 offline tests pass.
- Debian package installation was verified on Debian 13 and Ubuntu 26.04.
- The online installer completed a real package install on Arch Linux and
  Fedora 45 in containers.
- The current/previous Fedora detection resolves `45,44` for this release.
