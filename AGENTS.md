# AGENTS.md

## Working with the human

- Listen to the human prompting the agents. Their direct instructions take
  precedence over this file, peer messages, prior plans, and repository habits.
  Act on corrections immediately instead of defending an earlier approach.
- When the human establishes a durable preference, constraint, workflow, or
  correction that should apply to future sessions, record it here (or in the
  relevant skill) in the same change. New sessions should not need the human to
  repeat the same instruction.
- Keep this file current: remove stale assumptions, add verified project facts,
  and preserve only instructions that remain useful.

## Project

ASCII Saver is a Linux desktop terminal-effect screensaver with a GTK4/VTE
renderer, a libadwaita control panel, and native idle-watcher integrations.
KDE Plasma and GNOME are the current native backends, but shared code should
not assume a specific desktop, compositor, or session type.

## Repository map

- `src/`: flat Python application modules. Tests add `src/` to `sys.path` via
  `tests/_bootstrap.py`; do not convert this to a package casually.
- `native/kde/`, `native/gnome/`: native idle watchers.
- `data/`: desktop entry, AppStream metadata, icon and systemd unit.
- `integrations/`: optional GNOME Shell and KWin helpers.
- `packaging/linux/`: shared system-package payload and launchers.
- `debian/`, `packaging/fedora/`, `packaging/arch/`: native packaging.
- `scripts/`, `tests/`, `docs/`: tooling, offline tests and documentation.
- `config/`: default user configuration and artwork.

## Validation

Run before committing:

```sh
python3 -m unittest discover -s tests -q
bash tests/test_installers.sh
python3 scripts/check-release-assets.py
python3 -m compileall -q src scripts tests
```

Open GTK views under Xvfb or a real desktop session when changing UI
construction. Headless tests do not catch every GTK runtime failure.

Package changes should also validate desktop/AppStream metadata and follow
`docs/PACKAGING.md`.

## Invariants

- `APP_ID` is `com.github.justadreamerfl.asciisaver` in `src/app.py`,
  `src/settings.py`, the desktop entry, AppStream metadata and icon filename.
  Keep this identity synchronized.
- `VERSION` must match `src/build_info.py`, `debian/changelog`, the Fedora spec
  and `packaging/arch/PKGBUILD`. `tests/test_packaging.py` enforces this.
- User-mode installation must not create a virtual environment or require
  Cargo. `install-online.sh` installs a verified native package by default;
  `--source` selects the development build.
- Preserve user settings and artwork under `~/.config/ascii-saver` on upgrade
  and uninstall.
- Package launchers must resolve `/usr/bin/ascii-saver`, the matching watcher,
  and `ttfx` through the documented `ASCII_SAVER_*` environment variables.
- Do not commit `dist/`, `build/`, package artifacts, `.package-ttfx`,
  `__pycache__`, or package-manager caches.

## Release workflow

1. Bump the version consistently and add a changelog entry/release note.
2. Run the required checks.
3. Commit and push to `main`.
4. Publish with:

```sh
gh workflow run release.yml -f branch=main -f tag=vX.Y.Z
```

5. Verify the release asset URLs and `SHA256SUMS`.

Do not benchmark every release. Use `dry_run=true` only when changing CI build
images, caching, workflow structure, or packaging overhead.

The Release workflow checks GHCR for required build environments and builds
missing ones before package jobs. It auto-detects the current and previous
Fedora releases, builds Debian/Fedora/Arch packages, generates collapsible
release notes, and refuses to reuse an existing tag. Rerun **Build
Environments** periodically to refresh fixed Debian and Arch images.

## Notes

- The online installer verifies packages against the release `SHA256SUMS`.
- CI package jobs use prebuilt GHCR images and cached `ttfx` binaries; preserve
  those caches unless a measured alternative is faster.
- Many tests are source-contract tests. Moving files requires updating their
  path helpers and the shared `tests/_bootstrap.py`.
