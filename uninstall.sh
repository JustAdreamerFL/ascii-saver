#!/usr/bin/env bash
set -euo pipefail

data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
app_dir="$data_home/ascii-saver"
bin_dir="$HOME/.local/bin"
manage_session=true
remove_complete=true

usage() {
    cat <<'EOF'
Usage: ./uninstall.sh [OPTIONS]

Remove ASCII Saver for the current user. The configuration and custom ASCII
art in $XDG_CONFIG_HOME/ascii-saver (normally ~/.config/ascii-saver)
are always preserved.

Options:
  --no-stop           Do not contact the user service manager or running processes
  --non-interactive   Accepted for unattended removal (the script never prompts)
  -h, --help          Show this help

Set ASCII_SAVER_NO_SESSION=1 for the same behavior as --no-stop.
EOF
}

while (($#)); do
    case "$1" in
        --no-stop) manage_session=false ;;
        --non-interactive) ;;
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

case "${ASCII_SAVER_NO_SESSION:-0}" in
    1|true|TRUE|yes|YES) manage_session=false ;;
esac

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
                watcher_process_matches "$watcher_pid" "$expected_exe" && \
                    kill "$watcher_pid" 2>/dev/null || true
                if ! wait_for_watcher_exit "$watcher_pid" "$expected_exe"; then
                    printf 'The idle watcher did not stop within five seconds.\n' >&2
                    return 1
                fi
            fi
        fi
        rm -f -- "$pid_file"
    fi
}

has_user_systemd=false
if "$manage_session" && command -v systemctl >/dev/null && \
    systemctl --user show-environment >/dev/null 2>&1; then
    has_user_systemd=true
fi

if "$manage_session"; then
    "$bin_dir/ascii-saverctl" stop >/dev/null 2>&1 || true
    if "$has_user_systemd"; then
        systemctl --user disable --now ascii-saver.service >/dev/null 2>&1 || true
    fi
    if [[ -n "${XDG_RUNTIME_DIR:-}" ]]; then
        stop_watcher_pid_file "$XDG_RUNTIME_DIR/ascii-saver-watcher-$(id -u).pid"
    fi
    stop_watcher_pid_file "/tmp/ascii-saver-watcher-$(id -u).pid"
fi

# Remove only the optional KWin plugin owned by ASCII Saver; never touch the
# older KDE ASCII Saver KWin plugin or configuration keys.
if command -v kwriteconfig6 >/dev/null; then
    kwriteconfig6 --file kwinrc --group Plugins --key ascii-saver-fullscreenEnabled false || true
fi
if command -v kpackagetool6 >/dev/null; then
    kpackagetool6 --type=KWin/Script -r ascii-saver-fullscreen >/dev/null 2>&1 || true
fi
if command -v qdbus6 >/dev/null; then
    qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
fi
# Only remove exact paths owned by this installer. User configuration is separate
# and deliberately untouched so a reinstall restores the user's settings and art.
if [[ -d "$app_dir" && ! -L "$app_dir" ]]; then
    rm -rf -- "$app_dir"
elif [[ -e "$app_dir" || -L "$app_dir" ]]; then
    printf 'Not removing unexpected application path: %s\n' "$app_dir" >&2
    remove_complete=false
fi
rm -f -- "$data_home/applications/io.github.robbybobby77.AsciiSaver.desktop" \
    "$data_home/metainfo/io.github.robbybobby77.AsciiSaver.metainfo.xml" \
    "$data_home/icons/hicolor/scalable/apps/io.github.robbybobby77.AsciiSaver.svg" \
    "$bin_dir/ascii-saver" "$bin_dir/ascii-saverctl" \
    "$bin_dir/ascii-saver-watcher" "$bin_dir/ascii-saver-settings" \
    "$config_home/systemd/user/ascii-saver.service" \
    "$config_home/autostart/io.github.robbybobby77.AsciiSaver.Watcher.desktop" \
    "$config_home/autostart/ascii-saver-watcher.desktop"

update-desktop-database "$data_home/applications" 2>/dev/null || true
if "$manage_session" && "$has_user_systemd"; then
    systemctl --user daemon-reload
fi

printf 'ASCII Saver removed. Your settings and art are preserved in %s/ascii-saver\n' "$config_home"
if ! "$remove_complete"; then
    printf 'Some application files remain at %s; remove them only after inspecting that path.\n' "$app_dir" >&2
    exit 1
fi
