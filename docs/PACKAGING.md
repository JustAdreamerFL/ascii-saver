# Packaging

ASCII Saver has two installation models:

- **User mode:** `install-online.sh` detects the distribution, release and
  architecture, downloads the matching package, verifies it, and installs it
  with `apt`, `dnf` or `pacman`. No virtual environment or Cargo build runs on
  the installed machine.
- **Development mode:** `install.sh` (or `install-online.sh --source`) creates a
  private application directory with a virtual environment, compiles both native
  watchers and `ttfx`, and installs desktop integration under the user's home.
- **Distribution packages:** Debian, Fedora and Arch packages install
  system-wide under `/usr`, use the distribution Python/GTK runtime, and ship
  prebuilt watchers and `ttfx`.

## Shared payload

`packaging/linux/build-payload.sh DESTDIR` builds the filesystem tree used by
all three packages:

```text
/usr/bin/ascii-saver
/usr/bin/ascii-saverctl
/usr/bin/ascii-saver-settings
/usr/bin/ascii-saver-watcher
/usr/lib/ascii-saver/              # Python modules, ttfx, both watchers
/usr/share/applications/           # desktop entry
/usr/share/metainfo/               # AppStream metadata
/usr/share/icons/hicolor/          # application icon
/usr/share/kwin/scripts/           # optional KWin fullscreen helper
/usr/share/gnome-shell/extensions/ # optional cursor bridge
/etc/xdg/autostart/                # starts the watcher at login
```

`LIBDIR` overrides the payload library directory (Fedora uses `/usr/lib64`).
If `TTFX_BINARY` is set, or a `.package-ttfx` executable exists in the source
root, the payload uses that renderer instead of invoking Cargo. This is how the
CI package workflow avoids rebuilding Rust on every distribution.

The system launchers select `ascii-saver-watcher-gnome` or
`ascii-saver-watcher-kde` from `XDG_CURRENT_DESKTOP` and set
`ASCII_SAVER_PACKAGE_DIR`, `ASCII_SAVER_TTFX` and related paths. The watchers
use `/usr/bin/python3` when no bundled virtual environment exists.

## Build requirements

Common build dependencies: a C/C++ compiler, CMake, pkg-config, GLib, JSON-GLib,
Qt 6 and KDE Frameworks 6 KIdleTime development files. A modern Rust toolchain
is required only when building `ttfx` from source.

### Debian / Ubuntu

```sh
sudo apt install build-essential cargo cmake debhelper devscripts fakeroot \
  libglib2.0-dev libjson-glib-dev libkf6idletime-dev pkg-config \
  qt6-base-dev rustc
dpkg-buildpackage -us -uc -b
```

The package is written to the parent directory. The Debian package name and
dependencies are in `debian/control`.

### Fedora

```sh
sudo dnf install cargo cmake gcc-c++ glib2-devel json-glib-devel \
  kf6-kidletime-devel pkgconf-pkg-config qt6-qtbase-devel rpm-build rust
rpmbuild -bb packaging/fedora/ascii-saver.spec
```

### Arch Linux

```sh
sudo pacman -S --needed base-devel cargo cmake json-glib kidletime \
  pkgconf qt6-base
cd packaging/arch
makepkg -s
```

The version in `VERSION`, `debian/changelog`, the RPM spec and `PKGBUILD` must
match. `tests/test_packaging.py` enforces this for the repository.


## Choosing build distributions

The **Release** workflow defaults Debian to `debian:latest` and Arch to the
rolling `archlinux:base-devel`. For Fedora it reads the stable version from
`fedora:latest` and builds that release plus the previous one, so the newest
RPM is highlighted and the previous release is available in the collapsed
section. New Fedora releases therefore require no workflow edit.
Optional workflow inputs override each target:

- `debian_version` — any Debian/Ubuntu image tag (`trixie`, `bookworm`, ...)
- `fedora_versions` — comma-separated Fedora tags (`45,44`, `latest`, ...)
- `arch_image` — any Arch image tag (`base-devel`, dated base-devel tags, ...)

Each package job writes the resolved `PRETTY_NAME` to the workflow summary, so
a published release records exactly which distribution build was used.


## Supported package targets

| Family | Supported build targets | Notes |
|---|---|---|
| Debian | Debian 13 (trixie), selected with `debian_version` | Debian 12 is not supported because the KDE watcher needs KF6. |
| Fedora | Fedora 45 and 44 by default; any tags accepted in `fedora_versions` | The newest RPM is highlighted; older RPMs appear in a collapsed section. Update the default pair after each Fedora release. |
| Arch | Current rolling `base-devel` image | Arch has no supported point releases; older snapshots are not published. |

The release body is generated from the actual uploaded assets. It shows the
newest Debian, Fedora and Arch package in the main table, puts older Fedora
builds behind an expandable section, and adds expandable sections for source
archives and checksums.


## CI build images

The Release workflow runs distribution package jobs inside prebuilt images
published to GitHub Container Registry:

- `ghcr.io/justadreamerfl/ascii-saver-build-debian:latest`
- `ghcr.io/justadreamerfl/ascii-saver-build-fedora:<version>`
- `ghcr.io/justadreamerfl/ascii-saver-build-arch:base`

These images contain the compiler, CMake, Qt/KF6, GLib, JSON-GLib and packaging
tools. The **Build Environments** workflow rebuilds and publishes them. Run it
after changing build dependencies or adding a new Fedora release; otherwise a
new Fedora version has no matching prebuilt image.
