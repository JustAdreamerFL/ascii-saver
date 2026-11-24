# Installation and maintenance

## Before installing

### Distribution packages

Native packages install system-wide under `/usr` and ship prebuilt GNOME and
KDE watchers plus the instrumented `ttfx` renderer. The installed system needs
the declared Python/GTK runtime packages, but no virtual environment, compiler,
or Cargo toolchain. Remove the package with the distribution package manager
to leave no application files behind.

```sh
# Debian 13 / Ubuntu 26.04+
sudo apt install ./ascii-saver_0.113.0_amd64.deb

# Fedora 45 or 44
sudo dnf install ./ascii-saver-0.113.0-1.fc45.x86_64.rpm

# Arch Linux
sudo pacman -U ascii-saver-0.113.0-1-x86_64.pkg.tar.zst
```

The **Release** GitHub workflow builds both source archives and all three
package formats from a selected branch, then publishes them together. See [Packaging](PACKAGING.md) for local build requirements and the
shared payload layout.

### Development/source install

A source installation is user-local and needs a C++17 compiler, CMake 3.20 or
newer, Qt 6, KDE Frameworks 6 KIdleTime, Python 3 with virtual-environment
support, PyGObject, GTK 4, GTK4 VTE (`Vte 3.91`), and Rust/Cargo for `ttfx`.
GTK4 Layer Shell is optional but recommended for full panel coverage on Plasma
Wayland. When dependencies are missing, the interactive installer displays the
native package-manager command and asks before invoking it with `sudo`. Pass
`--no-install-deps` to keep dependency installation fully manual. See
[Distribution support](DISTRIBUTIONS.md) for exact package names.

## Recommended online install

```sh
curl -fsSL https://raw.githubusercontent.com/JustAdreamerFL/ascii-saver/main/install-online.sh | bash
```

This is the user installation mode. The bootstrap detects the distribution,
release and architecture, downloads the matching package from the latest
GitHub release, verifies it against the release `SHA256SUMS`, and installs it
with `apt`, `dnf` or `pacman`. It does not create a virtual environment or
build Rust/Python components. Supported native targets are Debian 13+,
Ubuntu 26.04+, Fedora with a published matching release, and Arch Linux
(including Arch derivatives).

The bootstrap requires Bash, `curl`, either `sha256sum` or `shasum`, the
distribution package manager, and either `sudo` or `pkexec` for authentication.
It stops on a missing or mismatched checksum. The checksum detects a damaged or
mismatched package; the GitHub repository and its release assets remain part of
the trust boundary.

Piping a network response to a shell is convenient but requires trusting that
URL at execution time. To review exactly what will run first:

```sh
curl -fsSLO https://raw.githubusercontent.com/JustAdreamerFL/ascii-saver/main/install-online.sh
less install-online.sh
bash install-online.sh
```

To install or roll back to a specific published release with the reviewed
bootstrap:

```sh
ASCII_SAVER_VERSION=v0.113.0 bash install-online.sh
```

The bootstrap also accepts `--version v0.113.0` and `--check` to verify the
selected package without installing it. If no matching native package exists,
rerun with `--source` to use the development/source installation path. Source
mode additionally accepts `--yes`, `--no-install-deps`, `--no-start`, and
`--non-interactive`. Run `bash install-online.sh --help` for the full list.

## Install from a Git clone

This route is useful for development or for reviewing the complete source:

```sh
git clone https://github.com/JustAdreamerFL/ascii-saver.git
cd ascii-saver
./scripts/dependency-hint.sh
./install.sh
```

The dependency helper only previews the package-manager command. If anything
is missing, `./install.sh` shows the same command and offers to run it.

To validate the required commands and GTK/VTE bindings without installing:

```sh
./install.sh --check
```

## Installed files

By default, installation creates:

```text
~/.local/bin/ascii-saver
~/.local/bin/ascii-saverctl
~/.local/bin/ascii-saver-watcher
~/.local/bin/ascii-saver-settings
~/.local/share/ascii-saver/
~/.local/share/applications/com.github.justadreamerfl.asciisaver.desktop
~/.local/share/metainfo/com.github.justadreamerfl.asciisaver.metainfo.xml
~/.local/share/icons/hicolor/scalable/apps/com.github.justadreamerfl.asciisaver.svg
~/.config/ascii-saver/config.json
~/.config/ascii-saver/logo.txt
~/.config/systemd/user/ascii-saver.service
```

On systems without a working systemd user manager, the last file is replaced
by `~/.config/autostart/com.github.justadreamerfl.asciisaver.Watcher.desktop`.
`XDG_CONFIG_HOME` and
`XDG_DATA_HOME` override the corresponding config and data roots. Command
wrappers remain in `~/.local/bin`.

The application virtual environment lives inside the data directory. Python
packages are not installed globally.

## Verify the installation

Provide a real keyboard or pointer event once after installation, then check:

```sh
ascii-saverctl status
ascii-saverctl preview
ascii-saverctl prefs
ascii-saverctl doctor
```

The first input is intentional: it arms the watcher without immediately
showing the saver when installation occurs on an already-idle session.

## Upgrade

Rerun the recommended online install command to install the current stable
release. The installer replaces application files and refreshes the idle
integration, but preserves:

```text
~/.config/ascii-saver/config.json
~/.config/ascii-saver/logo.txt
```

Application files are staged before replacement. If the replacement cannot
complete, the installer restores the previous application files and service
state.

For a Git clone, update the checkout and rerun the installer:

```sh
git pull --ff-only
./install.sh
```

Review release notes before upgrading. To return to an older release, use the
specific-version command above or download that release's source archive and
checksum from GitHub, verify it, and run its included `install.sh`. Back up the
config directory first when moving backward, because older releases may not
understand newer settings.

## Uninstall

From any directory after installation:

```sh
ascii-saverctl uninstall
```

Or, from a source checkout:

```sh
./uninstall.sh
```

Both methods remove the application, launchers, and idle integration while
preserving the configuration and artwork directory. Remove that directory
manually only if you no longer want the settings or artwork:

```sh
rm -r -- "${XDG_CONFIG_HOME:-$HOME/.config}/ascii-saver"
```

That last command is irreversible unless the directory is backed up.

## Offline installation

Download a release archive and its checksum on a connected computer, verify
the checksum there, and transfer both the verified archive and checksum to the
Plasma system. Published archives include the pinned TerminalTextEffects wheel,
so only distribution system dependencies must already be available. Extract
the archive and run `./install.sh --no-install-deps`.
