#!/usr/bin/env bash
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
py_src="$source_dir/src"
data_src="$source_dir/data"
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
app_dir="$data_home/ascii-saver"
bin_dir="$HOME/.local/bin"
systemd_dir="$config_home/systemd/user"
autostart_dir="$config_home/autostart"
applications_dir="$data_home/applications"
metainfo_dir="$data_home/metainfo"
icons_dir="$data_home/icons/hicolor/scalable/apps"
manage_session=true
check_only=false
detect_session_only=false
install_dependencies=true
assume_yes=false
non_interactive=false
dependencies_attempted=false
has_user_systemd=false
transaction_dir=
staged_app=
backup_app=
swap_complete=false
old_app_moved=false
install_complete=false
service_was_active=false
watcher_was_running=false
session_touched=false
started_watcher_pid=
# Always identify the active desktop and compositor. An unrecognized session
# must never silently fall back to the KDE watcher (and demand Qt/KF6).
source "$source_dir/scripts/detect-session.sh"
requested_backend=${ASCII_SAVER_BACKEND:-auto}
backend=

select_backend() {
    detect_desktop_session
    if [[ "$requested_backend" != auto && "$requested_backend" != kde && "$requested_backend" != gnome ]]; then
        printf 'Invalid ASCII_SAVER_BACKEND: %s (expected auto, kde, gnome)\n' "$requested_backend" >&2
        return 2
    fi
    if [[ "$requested_backend" == auto ]]; then
        backend=$session_backend
    else
        backend=$requested_backend
    fi
    if [[ "$backend" != kde && "$backend" != gnome ]]; then
        print_detected_session >&2
        printf '\nNo native idle watcher currently supports this desktop/compositor.\n' >&2
        printf 'Supported: KDE Plasma/KWin and GNOME/Mutter. Installation stopped before dependency checks.\n' >&2
        printf 'For diagnostics run: ./install.sh --detect-session\n' >&2
        return 2
    fi
    if [[ "$requested_backend" != auto && "$session_backend" != "$backend" ]]; then
        printf 'Warning: forcing %s backend on detected %s session.\n' "$backend" "$session_desktop" >&2
    fi
    printf 'Detected desktop: %s | compositor: %s | session: %s\n' \
        "$session_desktop" "$session_compositor" "$session_type"
    printf 'Selected idle watcher: %s\n' "$backend"
}

usage() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS]

Build and install ASCII Saver for the current user.

Options:
  --check             Check required system dependencies without installing
  --detect-session    Print detected desktop, compositor and watcher (no install)
  --yes               Install missing system dependencies without confirmation
  --no-install-deps   Print dependency guidance instead of offering to install it
  --no-start          Do not stop, enable, start, or reload session services
  --non-interactive   Never prompt; combine with --yes to install dependencies
  -h, --help          Show this help

Desktop and compositor are detected automatically from the graphical session.
Set ASCII_SAVER_BACKEND=gnome or kde only for troubleshooting.

Set ASCII_SAVER_NO_SESSION=1 for the same behavior as --no-start. This is
useful with an isolated HOME/XDG environment in package and installer tests.
EOF
}

while (($#)); do
    case "$1" in
        --check) check_only=true ;;
        --detect-session) detect_session_only=true ;;
        --yes) assume_yes=true ;;
        --no-install-deps) install_dependencies=false ;;
        --no-start) manage_session=false ;;
        --non-interactive) non_interactive=true ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if "$detect_session_only"; then
    detect_desktop_session
    print_detected_session
    if [[ "$session_backend" != kde && "$session_backend" != gnome ]]; then
        exit 2
    fi
    exit 0
fi

select_backend

case "${ASCII_SAVER_NO_SESSION:-0}" in
    1|true|TRUE|yes|YES) manage_session=false ;;
esac

show_dependency_help() {
    ASCII_SAVER_BACKEND="$backend" bash "$source_dir/scripts/dependency-hint.sh" >&2
}

check_dependencies() {
    local missing=false
    local command
    local -a commands=(python3)
    if [[ "$backend" == kde ]]; then
        commands+=(cmake c++)
    else
        commands+=(cc pkg-config)
    fi
    for command in "${commands[@]}"; do
        if ! command -v "$command" >/dev/null; then
            printf 'Missing required command: %s\n' "$command" >&2
            missing=true
        fi
    done
    if [[ "$backend" == gnome ]] && command -v pkg-config >/dev/null 2>&1; then
        if ! pkg-config --exists gio-2.0 json-glib-1.0; then
            printf 'Missing GNOME native development files: gio-2.0, json-glib-1.0.\n' >&2
            missing=true
        fi
    fi
    if "$missing"; then
        return 1
    fi

    if ! python3 - <<'PY'
import gi
for namespace, version in (("Gtk", "4.0"), ("Vte", "3.91"), ("Adw", "1"), ("PangoCairo", "1.0")):
    gi.require_version(namespace, version)
from gi.repository import PangoCairo  # Needed by the V97 mouse-drawing canvas
try:
    gi.require_version("Gtk4LayerShell", "1.0")
except ValueError:
    print("Warning: gtk4-layer-shell is unavailable; regular fullscreen windows will be used.")
PY
    then
        printf 'Missing required Python GTK 4, VTE 3.91, libadwaita 1 or PangoCairo bindings.\n' >&2
        return 1
    fi
}

install_system_dependencies() {
    local distro_id=unknown
    local distro_like=
    local answer=
    local needs_apt_update=false
    local ID=
    local ID_LIKE=
    local -a command=()
    if [[ -r /etc/os-release ]]; then
        # OS-provided values select a known package-manager command.
        source /etc/os-release
        distro_id=${ID:-unknown}
        distro_like=${ID_LIKE:-}
    fi

    case " $distro_id $distro_like " in
        *" fedora "*|*" rhel "*)
            if "$assume_yes"; then
                command=(sudo dnf --assumeyes install)
            else
                command=(sudo dnf install)
            fi
            command+=(python3 python3-pip python3-devel python3-gobject gtk4
                vte291-gtk4 libadwaita desktop-file-utils)
            if [[ "$backend" == kde ]]; then
                command+=(gcc-c++ cmake qt6-qtbase-devel kf6-kidletime-devel)
            else
                command+=(gcc pkgconf-pkg-config glib2-devel json-glib-devel)
            fi
            ;;
        *" debian "*|*" ubuntu "*)
            if ! command -v sudo >/dev/null || ! command -v apt-get >/dev/null; then
                show_dependency_help
                return 1
            fi
            needs_apt_update=true
            if "$assume_yes"; then
                command=(sudo apt-get -y install)
            else
                command=(sudo apt-get install)
            fi
            command+=(python3 python3-gi python3-venv gir1.2-gtk-4.0
                gir1.2-vte-3.91 gir1.2-adw-1 desktop-file-utils)
            if [[ "$backend" == kde ]]; then
                command+=(build-essential cmake qt6-base-dev libkf6idletime-dev)
            else
                command+=(build-essential pkg-config libglib2.0-dev libjson-glib-dev)
            fi
            ;;
        *" arch "*)
            if "$assume_yes"; then
                command=(sudo pacman --noconfirm -S --needed)
            else
                command=(sudo pacman -S --needed)
            fi
            command+=(python python-gobject gtk4 vte4 libadwaita desktop-file-utils)
            if [[ "$backend" == kde ]]; then
                command+=(base-devel cmake qt6-base kidletime)
            else
                command+=(base-devel pkgconf glib2 json-glib)
            fi
            ;;
        *" opensuse "*|*" suse "*)
            if "$assume_yes"; then
                command=(sudo zypper --non-interactive install)
            else
                command=(sudo zypper install)
            fi
            command+=(python3 python3-gobject typelib-1_0-Gtk-4_0
                typelib-1_0-Vte-3_91 typelib-1_0-Adw-1 desktop-file-utils)
            if [[ "$backend" == kde ]]; then
                command+=(gcc-c++ cmake qt6-base-devel kf6-kidletime-devel)
            else
                command+=(gcc pkgconf-pkg-config glib2-devel json-glib-devel)
            fi
            ;;
        *)
            printf 'Automatic dependency installation is unavailable for this distribution.\n' >&2
            show_dependency_help
            return 1
            ;;
    esac

    if ! command -v sudo >/dev/null; then
        printf 'sudo is required to install system dependencies automatically.\n' >&2
        show_dependency_help
        return 1
    fi

    printf 'Missing system dependencies. Proposed command:\n  '
    if "$needs_apt_update"; then
        printf 'sudo apt-get update\n  '
    fi
    printf '%q ' "${command[@]}"
    printf '\n'
    if ! "$assume_yes"; then
        if "$non_interactive" || [[ ! -r /dev/tty || ! -w /dev/tty ]]; then
            printf 'Rerun interactively, pass --yes, or install the dependencies above.\n' >&2
            return 1
        fi
        printf 'Install these packages now? [Y/n] ' >/dev/tty
        read -r answer </dev/tty || return 1
        case "$answer" in
            n|N|no|NO|No) return 1 ;;
        esac
    fi
    if "$needs_apt_update"; then
        if [[ -r /dev/tty ]]; then
            sudo apt-get update </dev/tty
        else
            sudo apt-get update
        fi
    fi
    dependencies_attempted=true
    if [[ -r /dev/tty ]]; then
        "${command[@]}" </dev/tty
    else
        "${command[@]}"
    fi
}

# Match the exact native watcher executable. Legacy Python match is for upgrades.
# Never signal a PID on a partial command-line substring.
watcher_process_matches() {
    local pid=$1 expected=$2 actual=
    local -a argv=()
    actual=$(readlink -f -- "/proc/$pid/exe" 2>/dev/null || true)
    if [[ -n "$actual" && "$actual" == "$expected" ]]; then
        return 0
    fi
    case "${actual##*/}" in
        python*) ;;
        *) return 1 ;;
    esac
    [[ -r "/proc/$pid/cmdline" ]] || return 1
    mapfile -d '' -t argv <"/proc/$pid/cmdline" || return 1
    [[ "${argv[1]:-}" == "$expected" ]]
}

wait_for_watcher_exit() {
    local watcher_pid=$1
    local expected_exe=$2
    local current_exe=
    local attempt
    for ((attempt=0; attempt<100; attempt++)); do
        if [[ ! -e "/proc/$watcher_pid/exe" ]]; then
            return 0
        fi
        if ! watcher_process_matches "$watcher_pid" "$expected_exe"; then
            return 0
        fi
        sleep 0.05
    done
    return 1
}

stop_watcher_pid_file() {
    local pid_file=$1
    local watcher_pid=
    local watcher_exe=
    local expected_exe=
    if [[ -r "$pid_file" ]]; then
        read -r watcher_pid <"$pid_file" || watcher_pid=
        if [[ "$watcher_pid" =~ ^[0-9]+$ ]] && [[ -e "/proc/$watcher_pid/exe" ]] && \
            [[ -e "$app_dir/ascii-saver-watcher" ]]; then
            watcher_exe=$(readlink -f -- "/proc/$watcher_pid/exe" 2>/dev/null || true)
            expected_exe=$(readlink -f -- "$app_dir/ascii-saver-watcher" 2>/dev/null || true)
            if watcher_process_matches "$watcher_pid" "$expected_exe"; then
                # Re-check immediately before signaling to reduce PID reuse risk.
                if watcher_process_matches "$watcher_pid" "$expected_exe"; then
                    watcher_was_running=true
                    kill "$watcher_pid" 2>/dev/null || true
                    if ! wait_for_watcher_exit "$watcher_pid" "$expected_exe"; then
                        printf 'The existing idle watcher did not stop within five seconds.\n' >&2
                        return 1
                    fi
                fi
            fi
        fi
        rm -f -- "$pid_file"
    fi
}

wait_for_watcher_start() {
    local launched_pid=$1
    local pid_file=
    local recorded_pid=
    local watcher_exe=
    local expected_exe=
    local attempt
    if [[ -z "${XDG_RUNTIME_DIR:-}" ]]; then
        return 1
    fi
    pid_file="$XDG_RUNTIME_DIR/ascii-saver-watcher-$(id -u).pid"
    expected_exe=$(readlink -f -- "$app_dir/ascii-saver-watcher" 2>/dev/null || true)
    for ((attempt=0; attempt<100; attempt++)); do
        if [[ -r "$pid_file" ]]; then
            read -r recorded_pid <"$pid_file" || recorded_pid=
            if [[ "$recorded_pid" =~ ^[0-9]+$ ]]; then
                if watcher_process_matches "$recorded_pid" "$expected_exe"; then
                    return 0
                fi
            fi
        fi
        if ! kill -0 "$launched_pid" 2>/dev/null; then
            return 1
        fi
        sleep 0.05
    done
    return 1
}

stop_existing_processes() {
    session_touched=true
    if [[ -x "$bin_dir/ascii-saverctl" ]]; then
        "$bin_dir/ascii-saverctl" stop >/dev/null 2>&1 || true
    fi
    if "$has_user_systemd"; then
        if systemctl --user is-active --quiet ascii-saver.service; then
            service_was_active=true
        fi
        systemctl --user stop ascii-saver.service 2>/dev/null || true
    fi
    if [[ -n "${XDG_RUNTIME_DIR:-}" ]]; then
        stop_watcher_pid_file "$XDG_RUNTIME_DIR/ascii-saver-watcher-$(id -u).pid"
    fi
    # Older releases fell back to /tmp; reap a leftover PID file on upgrade.
    stop_watcher_pid_file "/tmp/ascii-saver-watcher-$(id -u).pid"
}

managed_paths=()
managed_backups=()
managed_existed=()

remember_managed_file() {
    local target=$1
    local index=${#managed_paths[@]}
    local backup="$transaction_dir/managed-backup/$index"
    if [[ -e "$target" && ! -f "$target" && ! -L "$target" ]]; then
        printf 'Refusing to replace unexpected managed path: %s\n' "$target" >&2
        return 1
    fi
    managed_paths+=("$target")
    managed_backups+=("$backup")
    if [[ -e "$target" || -L "$target" ]]; then
        mkdir -p "$(dirname -- "$backup")"
        cp -a -- "$target" "$backup"
        managed_existed+=(1)
    else
        managed_existed+=(0)
    fi
}

install_managed_file() {
    local source=$1
    local target=$2
    local mode=$3
    local temporary
    temporary=$(mktemp "$(dirname -- "$target")/.ascii-saver-file.XXXXXX")
    if ! install -m "$mode" "$source" "$temporary"; then
        rm -f -- "$temporary"
        return 1
    fi
    mv -fT -- "$temporary" "$target"
}

write_managed_file() {
    local target=$1
    local mode=$2
    local temporary
    temporary=$(mktemp "$(dirname -- "$target")/.ascii-saver-file.XXXXXX")
    if ! cat >"$temporary"; then
        rm -f -- "$temporary"
        return 1
    fi
    chmod "$mode" "$temporary"
    mv -fT -- "$temporary" "$target"
}

restore_managed_files() {
    local index target
    for ((index=${#managed_paths[@]} - 1; index >= 0; index--)); do
        target=${managed_paths[$index]}
        rm -f -- "$target"
        if [[ "${managed_existed[$index]}" == 1 ]]; then
            mkdir -p "$(dirname -- "$target")"
            cp -a -- "${managed_backups[$index]}" "$target"
        fi
    done
}

cleanup() {
    local status=$?
    trap - EXIT INT TERM HUP
    if [[ "$install_complete" != true && -n "$started_watcher_pid" ]] && \
        kill -0 "$started_watcher_pid" 2>/dev/null; then
        kill "$started_watcher_pid" 2>/dev/null || true
        wait "$started_watcher_pid" 2>/dev/null || true
    fi
    if [[ "$install_complete" != true && ( "$swap_complete" == true || "$old_app_moved" == true ) ]]; then
        printf 'Installation did not complete; restoring the previous version.\n' >&2
        if [[ "$swap_complete" == true ]]; then
            restore_managed_files
            rm -rf -- "$app_dir"
        fi
        if [[ -d "$backup_app" ]]; then
            mv -- "$backup_app" "$app_dir"
        fi
    fi
    if [[ "$install_complete" != true ]] && "$manage_session" && "$session_touched"; then
        if "$has_user_systemd"; then
            systemctl --user daemon-reload >/dev/null 2>&1 || true
            if "$service_was_active"; then
                systemctl --user start ascii-saver.service >/dev/null 2>&1 || true
            fi
        elif "$watcher_was_running" && [[ -x "$bin_dir/ascii-saver-watcher" ]]; then
            nohup "$bin_dir/ascii-saver-watcher" >/dev/null 2>&1 &
        fi
    fi
    if [[ -n "$transaction_dir" && -d "$transaction_dir" ]]; then
        rm -rf -- "$transaction_dir"
    fi
    exit "$status"
}
trap cleanup EXIT INT TERM HUP

if ! check_dependencies; then
    if "$check_only" || ! "$install_dependencies"; then
        show_dependency_help
        exit 1
    fi
    if ! install_system_dependencies || ! check_dependencies; then
        printf 'Required dependencies are still unavailable.\n' >&2
        show_dependency_help
        exit 1
    fi
fi
if "$check_only"; then
    printf 'Required GTK/VTE runtime and %s watcher build dependencies are available.\n' "$backend"
    exit 0
fi

if "$manage_session" && command -v systemctl >/dev/null && \
    systemctl --user show-environment >/dev/null 2>&1; then
    has_user_systemd=true
elif ! "$manage_session" && command -v systemctl >/dev/null && \
    [[ -n "${XDG_RUNTIME_DIR:-}" && -S "$XDG_RUNTIME_DIR/systemd/private" ]]; then
    # In --no-start mode detect the normal integration without contacting the
    # live manager. All files still honor the supplied HOME/XDG paths.
    has_user_systemd=true
fi

mkdir -p "$data_home" "$config_home"
transaction_dir=$(mktemp -d "$data_home/.ascii-saver-install.XXXXXX")
chmod 0700 "$transaction_dir"
staged_app="$transaction_dir/app"
backup_app="$transaction_dir/previous-app"
build_dir="$transaction_dir/build"
mkdir -p "$staged_app"

configure_watcher() {
    cmake -S "$source_dir/native/kde" -B "$build_dir" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$staged_app" \
        -DCMAKE_INSTALL_BINDIR=.
}

if [[ "$backend" == kde ]]; then
    if ! configure_watcher; then
        printf 'Unable to configure the Qt 6/KF6 watcher build. See CMake errors above.\n' >&2
        exit 1
    fi
    if ! cmake --build "$build_dir" --parallel; then
        printf 'Unable to build the Qt 6/KF6 watcher.\n' >&2
        exit 1
    fi
    if ! cmake --install "$build_dir"; then
        printf 'Unable to stage the Qt 6/KF6 watcher.\n' >&2
        exit 1
    fi
else
    printf 'GNOME session: building native C/GIO Mutter IdleMonitor watcher (no Qt/KF6 required).\n'
    # pkg-config returns compiler/linker flags, not shell fragments. These are
    # package-defined tokens (not user input), so splitting into an array is safe.
    read -r -a native_cflags <<< "$(pkg-config --cflags gio-2.0 json-glib-1.0)"
    read -r -a native_libs <<< "$(pkg-config --libs gio-2.0 json-glib-1.0)"
    if ! cc -std=gnu11 -O2 -Wall -Wextra -Werror=implicit-function-declaration \
         -DASCII_SAVER_VERSION=\"$(head -n 1 "$source_dir/VERSION")\" \
         "${native_cflags[@]}" "$source_dir/native/gnome/gnome_idle_watcher.c" \
         -o "$staged_app/ascii-saver-watcher" "${native_libs[@]}"; then
        printf 'Failed to compile the GNOME C/GIO idle watcher.\n' >&2
        exit 1
    fi
    chmod 0755 "$staged_app/ascii-saver-watcher"
fi

if ! python3 -m venv --system-site-packages "$staged_app/venv"; then
    printf 'Unable to create a Python virtual environment.\n' >&2
    show_dependency_help
    exit 1
fi
# Always install the instrumented renderer included with this release.
# A system ttfx may not understand --stats-file, --time-scale, or --duration-factor.
# A trusted, explicitly selected binary is allowed only after capability checks.
ttfx_binary=${ASCII_SAVER_TTFX:-}
if [[ -z "$ttfx_binary" ]]; then
    if ! command -v cargo >/dev/null 2>&1; then
        printf 'Cargo is required to build the bundled instrumented ttfx renderer.\n' >&2
        printf 'On Arch/CachyOS, install Rust and Cargo with: sudo pacman -S rust cargo\n' >&2
        exit 1
    fi
    printf 'Building bundled instrumented ttfx renderer...\n'
    # Preserve Cargo artifacts across releases. Staged install safety is
    # unaffected: only a verified executable is copied to the transaction.
    cache_home="${XDG_CACHE_HOME:-$HOME/.cache}"
    new_cache="$cache_home/ascii-saver"
    cargo_target_dir="$new_cache/cargo-target"
    mkdir -p "$cargo_target_dir"
    printf 'Using persistent Rust build cache: %s\n' "$cargo_target_dir"
    if ! CARGO_TARGET_DIR="$cargo_target_dir" cargo build \
        --manifest-path "$source_dir/ttfx-rust/Cargo.toml" --release --locked; then
        printf 'The bundled ttfx Rust build failed. Existing installation was not replaced.\n' >&2
        exit 1
    fi
    ttfx_binary="$cargo_target_dir/release/ttfx"
fi
if [[ ! -f "$ttfx_binary" || ! -x "$ttfx_binary" ]]; then
    printf 'Instrumented ttfx binary is missing or not executable: %s\n' "$ttfx_binary" >&2
    exit 1
fi
if ! ttfx_help=$("$ttfx_binary" --help 2>&1); then
    printf 'Could not run the bundled ttfx binary for capability checking.\n' >&2
    exit 1
fi
for feature in '--stats-file' '--time-scale' '--duration-factor'; do
    if [[ "$ttfx_help" != *"$feature"* ]]; then
        printf 'Incompatible ttfx binary: missing %s. Refusing to install.\n' "$feature" >&2
        exit 1
    fi
done
install -m 0755 "$ttfx_binary" "$staged_app/venv/bin/ttfx"
ln -s ttfx "$staged_app/venv/bin/tte"

install -m 0644 "$py_src/screen_lock_backend.py" "$staged_app/screen_lock_backend.py"
install -m 0644 "$py_src/effect_rotation.py" "$staged_app/effect_rotation.py"
install -m 0644 "$py_src/preview_sequence.py" "$staged_app/preview_sequence.py"
install -m 0644 "$py_src/status_model.py" "$staged_app/status_model.py"
install -m 0644 "$py_src/dashboard_playback.py" "$staged_app/dashboard_playback.py"
install -m 0755 "$py_src/app.py" "$staged_app/app.py"
install -m 0755 "$py_src/cli.py" "$staged_app/cli.py"
install -m 0755 "$py_src/ctl.py" "$staged_app/ctl.py"
install -m 0755 "$py_src/settings.py" "$staged_app/settings.py"
# Preprocessed low-memory RGBA previews: GTK never decodes GIFs or starts Glycin.
mkdir -p "$staged_app/effects"
for pack in "$source_dir"/preview-packs/*.aspr; do
    [[ -f "$pack" ]] || continue
    install -m 0644 "$pack" "$staged_app/effects/$(basename "$pack")"
done
if [[ $(find "$staged_app/effects" -maxdepth 1 -name '*.aspr' | wc -l) -ne 37 ]]; then
    printf 'Missing packed effect previews; expected 37 assets.\n' >&2
    exit 1
fi
install -m 0755 "$source_dir/uninstall.sh" "$staged_app/uninstall.sh"
install -m 0644 "$py_src/helpers.py" "$staged_app/helpers.py"
install -m 0644 "$py_src/window_shortcuts.py" "$staged_app/window_shortcuts.py"
install -m 0644 "$py_src/artwork_history.py" "$staged_app/artwork_history.py"
install -m 0644 "$py_src/artwork_selection.py" "$staged_app/artwork_selection.py"
install -m 0644 "$py_src/palette_editor_model.py" "$staged_app/palette_editor_model.py"
install -m 0644 "$py_src/adwaita_ui.py" "$staged_app/adwaita_ui.py"
install -m 0644 "$py_src/monitor_labels.py" "$staged_app/monitor_labels.py"
install -m 0644 "$py_src/monitor_config.py" "$staged_app/monitor_config.py"
# Modular libadwaita screens, state tracking, preview and diagnostics.
for module in effect_catalog preferences_model preferences_shell preferences_controls preferences_pages preferences_state preferences_gallery preferences_gallery_view preferences_displays preferences_actions preferences_defaults artwork_library artwork_catalog artwork_library_view artwork_online artwork_online_view artwork_editor artwork_editor_io artwork_retouch artwork_canvas artwork_canvas_view artwork_templates artwork_templates_view photo_ascii photo_ascii_view photo_project photo_presets diagnostics_model diagnostics_view measurements_ui; do
    install -m 0644 "$py_src/$module.py" "$staged_app/$module.py"
done
install -m 0644 "$py_src/final_frame.py" "$staged_app/final_frame.py"
install -m 0644 "$py_src/artwork_fit.py" "$staged_app/artwork_fit.py"
install -m 0644 "$py_src/palette_engine.py" "$staged_app/palette_engine.py"
install -m 0644 "$py_src/edit_state.py" "$staged_app/edit_state.py"
install -m 0644 "$py_src/playlist_engine.py" "$staged_app/playlist_engine.py"
install -m 0644 "$py_src/effect_selection.py" "$staged_app/effect_selection.py"
install -m 0644 "$py_src/effect_library.py" "$staged_app/effect_library.py"
install -m 0644 "$py_src/effect_metadata.py" "$staged_app/effect_metadata.py"
install -m 0644 "$py_src/animated_preview.py" "$staged_app/animated_preview.py"
install -m 0644 "$py_src/preview_asset.py" "$staged_app/preview_asset.py"
install -m 0644 "$py_src/preview_tint.py" "$staged_app/preview_tint.py"
install -m 0644 "$py_src/spawn_events.py" "$staged_app/spawn_events.py"
install -m 0644 "$py_src/frame_report.py" "$staged_app/frame_report.py"
install -m 0644 "$py_src/gpu_accounting.py" "$staged_app/gpu_accounting.py"
install -m 0644 "$py_src/effect_profiles.py" "$staged_app/effect_profiles.py"
install -m 0644 "$py_src/measured_playlists.py" "$staged_app/measured_playlists.py"
install -m 0644 "$py_src/playlist_editor.py" "$staged_app/playlist_editor.py"
install -m 0644 "$py_src/playlist_gallery_model.py" "$staged_app/playlist_gallery_model.py"
install -m 0644 "$py_src/effect_preview_window.py" "$staged_app/effect_preview_window.py"
install -m 0644 "$py_src/auto_playlists.py" "$staged_app/auto_playlists.py"
for module in performance_logger performance_ui performance_series performance_summary effect_timing; do
    install -m 0644 "$py_src/$module.py" "$staged_app/$module.py"
done
install -m 0644 "$source_dir/VERSION" "$staged_app/VERSION"
install -m 0644 "$py_src/build_info.py" "$staged_app/build_info.py"
install -m 0644 "$py_src/component_versions.py" "$staged_app/component_versions.py"
install -m 0644 "$py_src/gnome_dock.py" "$staged_app/gnome_dock.py"
install -m 0644 "$py_src/gnome_cursor_bridge.py" "$staged_app/gnome_cursor_bridge.py"
install -m 0644 "$py_src/app_menu.py" "$staged_app/app_menu.py"
install -m 0644 "$py_src/application_actions.py" "$staged_app/application_actions.py"
printf "%s\n" "$backend" > "$staged_app/watcher-backend"

# Rust ttfx is already installed in staged_app/venv/bin.
# This application has its own identity. Never import or delete data from
# the older KDE ASCII Saver. The user can uninstall that version separately.
# Existing ascii-saver preferences are preserved on upgrades.

mkdir -p "$bin_dir" "$config_home/ascii-saver" "$applications_dir" \
    "$metainfo_dir" "$icons_dir"
if "$has_user_systemd"; then
    mkdir -p "$systemd_dir"
else
    mkdir -p "$autostart_dir"
fi

remember_managed_file "$bin_dir/ascii-saver"
remember_managed_file "$bin_dir/ascii-saverctl"
remember_managed_file "$bin_dir/ascii-saver-watcher"
remember_managed_file "$bin_dir/ascii-saver-settings"
remember_managed_file "$applications_dir/com.github.justadreamerfl.asciisaver.desktop"
remember_managed_file "$metainfo_dir/com.github.justadreamerfl.asciisaver.metainfo.xml"
remember_managed_file "$icons_dir/com.github.justadreamerfl.asciisaver.svg"
remember_managed_file "$systemd_dir/ascii-saver.service"
remember_managed_file "$autostart_dir/com.github.justadreamerfl.asciisaver.Watcher.desktop"
remember_managed_file "$autostart_dir/ascii-saver-watcher.desktop"
# The previous desktop identity is backed up so a failed upgrade can restore it.
remember_managed_file "$applications_dir/io.github.robbybobby77.AsciiSaver.desktop"
remember_managed_file "$metainfo_dir/io.github.robbybobby77.AsciiSaver.metainfo.xml"
remember_managed_file "$icons_dir/io.github.robbybobby77.AsciiSaver.svg"
remember_managed_file "$autostart_dir/io.github.robbybobby77.AsciiSaver.Watcher.desktop"

if [[ -e "$app_dir" || -L "$app_dir" ]]; then
    if [[ -L "$app_dir" || ! -d "$app_dir" ]]; then
        printf 'Refusing to replace unexpected application path: %s\n' "$app_dir" >&2
        exit 1
    fi
fi

if "$manage_session"; then
    stop_existing_processes
fi

if [[ -e "$app_dir" || -L "$app_dir" ]]; then
    mv -- "$app_dir" "$backup_app"
    old_app_moved=true
fi
mv -- "$staged_app" "$app_dir"
swap_complete=true

install_managed_file "$source_dir/bin/ascii-saver" "$bin_dir/ascii-saver" 0755
install_managed_file "$source_dir/bin/ascii-saverctl" "$bin_dir/ascii-saverctl" 0755
install_managed_file "$source_dir/bin/ascii-saver-watcher" "$bin_dir/ascii-saver-watcher" 0755
install_managed_file "$source_dir/bin/ascii-saver-settings" \
    "$bin_dir/ascii-saver-settings" 0755

if [[ ! -e "$config_home/ascii-saver/config.json" && \
    ! -L "$config_home/ascii-saver/config.json" ]]; then
    install_managed_file "$source_dir/config/config.json" \
        "$config_home/ascii-saver/config.json" 0644
fi
if [[ ! -e "$config_home/ascii-saver/logo.txt" && \
    ! -L "$config_home/ascii-saver/logo.txt" ]]; then
    install_managed_file "$source_dir/config/logo.txt" \
        "$config_home/ascii-saver/logo.txt" 0644
fi

escaped_app=$(printf '%s' "$bin_dir/ascii-saver" | sed 's/[&|]/\\&/g')
sed "s|@APP@|$escaped_app|" \
    "$data_src/com.github.justadreamerfl.asciisaver.desktop.in" \
    | write_managed_file \
        "$applications_dir/com.github.justadreamerfl.asciisaver.desktop" 0644
install_managed_file "$data_src/com.github.justadreamerfl.asciisaver.metainfo.xml" \
    "$metainfo_dir/com.github.justadreamerfl.asciisaver.metainfo.xml" 0644
install_managed_file "$data_src/icons/com.github.justadreamerfl.asciisaver.svg" \
    "$icons_dir/com.github.justadreamerfl.asciisaver.svg" 0644
# Use a full path: icon themes and external launchers sometimes fail to resolve
# a custom theme-name icon even though Plasma's task manager does.
python3 - "$applications_dir/com.github.justadreamerfl.asciisaver.desktop" "$icons_dir/com.github.justadreamerfl.asciisaver.svg" <<'ICON_FIX'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); icon=pathlib.Path(sys.argv[2])
content=p.read_text()
content=content.replace("Icon=com.github.justadreamerfl.asciisaver",f"Icon={icon}")
p.write_text(content)
ICON_FIX
# Remove files installed under the pre-rename desktop identity.
rm -f -- "$applications_dir/io.github.robbybobby77.AsciiSaver.desktop" \
    "$metainfo_dir/io.github.robbybobby77.AsciiSaver.metainfo.xml" \
    "$icons_dir/io.github.robbybobby77.AsciiSaver.svg" \
    "$autostart_dir/io.github.robbybobby77.AsciiSaver.Watcher.desktop"
update-desktop-database "$applications_dir" 2>/dev/null || true

if "$has_user_systemd"; then
    if [[ "$backend" == gnome ]]; then
        service_source="$data_src/systemd/gnome-ascii-saver.service"
    else
        service_source="$data_src/systemd/ascii-saver.service"
    fi
    install_managed_file "$service_source" \
        "$systemd_dir/ascii-saver.service" 0644
    rm -f -- "$autostart_dir/com.github.justadreamerfl.asciisaver.Watcher.desktop" \
        "$autostart_dir/ascii-saver-watcher.desktop"
    integration='systemd user service'
    if "$manage_session"; then
        systemctl --user daemon-reload
        # Re-enable removes a stale Plasma WantedBy symlink after switching DEs.
        systemctl --user reenable ascii-saver.service
        systemctl --user start ascii-saver.service
    fi
else
    rm -f -- "$systemd_dir/ascii-saver.service"
    escaped_watcher=$(printf '%s' "$bin_dir/ascii-saver-watcher" | sed 's/[&|]/\\&/g')
    sed "s|@WATCHER@|$escaped_watcher|" \
        "$data_src/com.github.justadreamerfl.asciisaver.Watcher.desktop.in" \
        | sed "s|OnlyShowIn=KDE;|OnlyShowIn=$([[ "$backend" == gnome ]] && echo 'GNOME;' || echo 'KDE;')|" \
        | write_managed_file \
            "$autostart_dir/com.github.justadreamerfl.asciisaver.Watcher.desktop" 0644
    rm -f -- "$autostart_dir/ascii-saver-watcher.desktop"
    integration='XDG session autostart'
    if "$manage_session"; then
        nohup "$bin_dir/ascii-saver-watcher" >/dev/null 2>&1 &
        started_watcher_pid=$!
        if ! wait_for_watcher_start "$started_watcher_pid"; then
            printf 'The XDG idle watcher did not start successfully.\n' >&2
            exit 1
        fi
    fi
fi

install_complete=true
rm -rf -- "$backup_app"
# No legacy cleanup here: other application identities are user-managed.
# In particular we must not stop, remove, or migrate any kde-ascii-saver paths.

printf '\nASCII Saver %s installed.\n' "$(head -n 1 "$app_dir/VERSION")"
printf 'Idle integration: %s (%s)\n' "$integration" "$backend"
if "$manage_session"; then
    printf 'The idle watcher will arm after your next keyboard or pointer input.\n'
else
    printf 'Session integration was installed but not started (--no-start).\n'
fi
printf 'Start now:  %s/ascii-saverctl start\n' "$bin_dir"
printf 'Control:    %s/ascii-saverctl prefs\n' "$bin_dir"
printf 'Edit art:   %s/ascii-saverctl edit\n' "$bin_dir"
printf 'Set delay:  %s/ascii-saverctl delay 180\n' "$bin_dir"
printf 'If those commands are not found, add %s to PATH.\n' "$bin_dir"

if "$manage_session" && ! "$non_interactive" && ! "$assume_yes" && \
    [[ -r /dev/tty && -w /dev/tty ]]; then
    printf 'Open a windowed preview now? [Y/n] ' >/dev/tty
    read -r preview_answer </dev/tty || preview_answer=n
    case "$preview_answer" in
        n|N|no|NO|No) ;;
        *) "$bin_dir/ascii-saverctl" preview || true ;;
    esac
fi

# Optional fullscreen protection for KWin Wayland/X11. Never fail application installation.
if [[ "$backend" == kde && "$check_only" == false && "$manage_session" == true ]]; then
    if command -v kpackagetool6 >/dev/null && command -v kwriteconfig6 >/dev/null; then
        kpackagetool6 --type=KWin/Script -u "$source_dir/integrations/kwin-fullscreen" >/dev/null 2>&1 \
            || kpackagetool6 --type=KWin/Script -i "$source_dir/integrations/kwin-fullscreen" >/dev/null 2>&1 \
            || printf 'Optional fullscreen helper installation failed.
' >&2
        kwriteconfig6 --file kwinrc --group Plugins --key ascii-saver-fullscreenEnabled true
        if command -v qdbus6 >/dev/null; then
            qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
        fi
    else
        printf 'KWin script tools missing: fullscreen protection requires manual setup.
' >&2
    fi
fi
