# Packaging

ASCII Saver has two installation models:

- **Development/user-local:** `install.sh` / `install-online.sh` create a
  private application directory with a virtual environment, compile both native
  watchers and `ttfx`, and install desktop integration under the user's home.
- **Distribution packages:** Debian, Fedora and Arch packages install
  system-wide under `/usr`, use the distribution Python/GTK runtime, and ship
  prebuilt watchers and `ttfx`. No virtual environment or Cargo build runs on
  the installed machine.

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
