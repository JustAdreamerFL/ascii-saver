#!/usr/bin/env bash
# Optional user-initiated GNOME Shell extension install / removal.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_dir=$(cd "$script_dir/.." && pwd)
uuid='ascii-saver-cursor@ascii-saver.local'
target="${XDG_DATA_HOME:-$HOME/.local/share}/gnome-shell/extensions/$uuid"

if [[ "${1:-}" == '--remove' ]]; then
    if command -v gnome-extensions >/dev/null 2>&1; then
        gnome-extensions disable "$uuid" 2>/dev/null || true
    fi
    if [[ -d "$target" ]]; then
        rm -- "$target/metadata.json" "$target/extension.js" 2>/dev/null || true
        rmdir -- "$target" 2>/dev/null || true
    fi
    printf 'GNOME cursor bridge files removed. Log out/in if necessary.\n'
    exit 0
fi
if [[ $# -ne 0 ]]; then
    printf 'Usage: %s [--remove]\n' "$0" >&2
    exit 2
fi
if [[ ":${XDG_CURRENT_DESKTOP:-}:" != *GNOME* && "${XDG_SESSION_DESKTOP:-}" != gnome* ]]; then
    printf 'This optional bridge is intended for an active GNOME desktop.\n' >&2
    exit 1
fi
if ! command -v gnome-extensions >/dev/null 2>&1; then
    printf 'gnome-extensions command not found. Install GNOME Shell extension tools.\n' >&2
    exit 1
fi
if command -v gnome-shell >/dev/null 2>&1; then
    version=$(gnome-shell --version | grep -oE '[0-9]+' | head -1 || true)
    if [[ -n "$version" && ( "$version" -lt 49 || "$version" -gt 51 ) ]]; then
        printf 'This bridge targets GNOME Shell 49-51; found GNOME Shell %s.\n' "$version" >&2
        exit 1
    fi
fi
mkdir -p -- "$target"
install -m 0644 "$source_dir/gnome-shell-extension/$uuid/extension.js" "$target/extension.js"
install -m 0644 "$source_dir/gnome-shell-extension/$uuid/metadata.json" "$target/metadata.json"
printf 'Installed optional GNOME cursor bridge to %s\n' "$target"
if gnome-extensions enable "$uuid" 2>/dev/null; then
    printf 'Enabled the extension. GNOME fullscreen cursor hiding is now available.\n'
else
    printf 'GNOME may need a logout/login before it discovers the new extension.\n'
    printf 'After logging back in: gnome-extensions enable %s\n' "$uuid"
fi
printf 'To remove: bash "%s" --remove\n' "$0"
