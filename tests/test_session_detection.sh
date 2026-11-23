#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
tmp_dir=$(mktemp -d)
trap 'rm -rf -- "$tmp_dir"' EXIT

# Noninteractive: --detect-session must not test/install any dependencies or
# contact running services. Avoid inheriting the test runner's desktop session.
check() {
    local wanted=$1
    local source_marker=$2
    shift 2
    local output
    output=$(env -i HOME="$tmp_dir" PATH="/usr/bin:/bin" "$@" \
        "$project_dir/install.sh" --detect-session)
    [[ "$output" == *"Idle watcher backend: $wanted"* ]] || {
        printf 'Incorrect backend for %s:\n%s\n' "$*" "$output" >&2
        exit 1
    }
    [[ "$output" == *"Detection: $source_marker"* ]] || {
        printf 'Incorrect detection source for %s:\n%s\n' "$*" "$output" >&2
        exit 1
    }
}

check 'GNOME (C/GLib/Mutter)' XDG_CURRENT_DESKTOP \
    XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_TYPE=wayland
check 'GNOME (C/GLib/Mutter)' XDG_CURRENT_DESKTOP \
    XDG_CURRENT_DESKTOP=ubuntu:GNOME XDG_SESSION_DESKTOP=plasma
check 'KDE (C++/KIdleTime)' XDG_CURRENT_DESKTOP \
    XDG_CURRENT_DESKTOP=KDE:Plasma XDG_SESSION_DESKTOP=gnome
check 'KDE (C++/KIdleTime)' XDG_SESSION_DESKTOP \
    XDG_SESSION_DESKTOP=plasmawayland XDG_SESSION_TYPE=wayland
check 'GNOME (C/GLib/Mutter)' DESKTOP_SESSION \
    DESKTOP_SESSION=gnome-classic
check 'GNOME (C/GLib/Mutter)' XDG_CURRENT_DESKTOP \
    XDG_CURRENT_DESKTOP=GNOME:KDE

for compositor in Hyprland sway niri COSMIC gnome-flashback; do
    output_file="$tmp_dir/${compositor}.txt"
    if env -i HOME="$tmp_dir" PATH="/usr/bin:/bin" \
        XDG_CURRENT_DESKTOP="$compositor" XDG_SESSION_TYPE=wayland \
        "$project_dir/install.sh" --detect-session >"$output_file" 2>&1; then
        printf 'Unsupported compositor unexpectedly accepted: %s\n' "$compositor" >&2
        exit 1
    fi
    grep -q 'unsupported' "$output_file"
done

if env -i HOME="$tmp_dir" PATH="/usr/bin:/bin" \
    XDG_CURRENT_DESKTOP=unknown-does-not-exist \
    "$project_dir/install.sh" --check >"$tmp_dir/unknown.txt" 2>&1; then
    echo 'Unknown session unexpectedly defaulted to KDE' >&2
    exit 1
fi
grep -q 'No native idle watcher currently supports this desktop/compositor' "$tmp_dir/unknown.txt"

printf 'Desktop/compositor autodetection tests passed.\n'

output=$(env -i HOME="$tmp_dir" PATH="/usr/bin:/bin" \
    XDG_CURRENT_DESKTOP=GNOME WAYLAND_DISPLAY=wayland-1 \
    "$project_dir/install.sh" --detect-session)
[[ "$output" == *'Session type: wayland'* ]] || {
    echo 'Missing Wayland session type fallback' >&2
    exit 1
}
