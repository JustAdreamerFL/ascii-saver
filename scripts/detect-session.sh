#!/usr/bin/env bash
# Detect the active desktop session without depending on Qt, GNOME or Python.
# Source this file and call detect_desktop_session; or run it for a diagnostic.
# XDG_CURRENT_DESKTOP is a colon-separated, ordered list (freedesktop spec).

session_classify() {
    local value=${1,,}
    case "$value" in
        kde|plasma|plasmawayland|plasmax11|kde-plasma)
            session_desktop='KDE Plasma'; session_compositor='KWin'; session_backend=kde ;;
        gnome-flashback|gnome-flashback-*)
            session_desktop='GNOME Flashback'; session_compositor='Metacity/unknown'; session_backend=unsupported ;;
        gnome|gnome-classic|gnome-wayland|gnome-xorg|gnome-shell|ubuntu|ubuntu-wayland|ubuntu-xorg)
            session_desktop='GNOME'; session_compositor='Mutter (GNOME Shell)'; session_backend=gnome ;;
        sway|swayfx)
            session_desktop='Sway'; session_compositor='Sway'; session_backend=unsupported ;;
        hyprland)
            session_desktop='Hyprland'; session_compositor='Hyprland'; session_backend=unsupported ;;
        niri)
            session_desktop='niri'; session_compositor='niri'; session_backend=unsupported ;;
        river)
            session_desktop='river'; session_compositor='river'; session_backend=unsupported ;;
        labwc)
            session_desktop='labwc'; session_compositor='labwc'; session_backend=unsupported ;;
        wayfire)
            session_desktop='Wayfire'; session_compositor='Wayfire'; session_backend=unsupported ;;
        weston)
            session_desktop='Weston'; session_compositor='Weston'; session_backend=unsupported ;;
        cosmic|cosmic-*)
            session_desktop='COSMIC'; session_compositor='cosmic-comp'; session_backend=unsupported ;;
        xfce|xfce4|xubuntu)
            session_desktop='Xfce'; session_compositor='Xfwm4'; session_backend=unsupported ;;
        cinnamon)
            session_desktop='Cinnamon'; session_compositor='Muffin'; session_backend=unsupported ;;
        mate)
            session_desktop='MATE'; session_compositor='Marco'; session_backend=unsupported ;;
        lxqt)
            session_desktop='LXQt'; session_compositor='Unknown'; session_backend=unsupported ;;
        *) return 1 ;;
    esac
    return 0
}

detect_desktop_session() {
    session_backend=unknown
    session_desktop=unknown
    session_compositor=unknown
    session_type=${XDG_SESSION_TYPE:-unknown}
    if [[ "$session_type" == unknown ]]; then
        if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
            session_type=wayland
        elif [[ -n "${DISPLAY:-}" ]]; then
            session_type=x11
        fi
    fi
    session_source='not detected'
    local part
    local -a desktop_parts=()

    # Most accurate. The standard permits entries like GNOME:GNOME-Classic
    # or KDE:Plasma. Consider each exact component in order.
    if [[ -n "${XDG_CURRENT_DESKTOP:-}" ]]; then
        IFS=':' read -r -a desktop_parts <<< "$XDG_CURRENT_DESKTOP"
        for part in "${desktop_parts[@]}"; do
            if session_classify "$part"; then
                session_source=XDG_CURRENT_DESKTOP
                return 0
            fi
        done
    fi

    # Useful for launchers which omit XDG_CURRENT_DESKTOP.
    for part in "${XDG_SESSION_DESKTOP:-}" "${DESKTOP_SESSION:-}"; do
        [[ -n "$part" ]] || continue
        if session_classify "$part"; then
            if [[ "$part" == "${XDG_SESSION_DESKTOP:-}" ]]; then
                session_source=XDG_SESSION_DESKTOP
            else
                session_source=DESKTOP_SESSION
            fi
            return 0
        fi
    done

    # Process inspection is only a fallback: several logins may run under
    # one account. A recognized XDG session always wins over this heuristic.
    if command -v pgrep >/dev/null 2>&1; then
        local uid
        uid=$(id -u)
        local gnome_found=false kde_found=false other_name=
        pgrep -u "$uid" -x gnome-shell >/dev/null 2>&1 && gnome_found=true
        if pgrep -u "$uid" -x kwin_wayland >/dev/null 2>&1 || \
           pgrep -u "$uid" -x kwin_x11 >/dev/null 2>&1; then
            kde_found=true
        fi
        if "$gnome_found" && ! "$kde_found"; then
            session_classify gnome
            session_source='running gnome-shell process (fallback)'
        elif "$kde_found" && ! "$gnome_found"; then
            session_classify kde
            session_source='running KWin process (fallback)'
        else
            for part in Hyprland sway niri river labwc wayfire weston cosmic-comp; do
                if pgrep -u "$uid" -x "$part" >/dev/null 2>&1; then
                    other_name=$part
                    break
                fi
            done
            if [[ -n "$other_name" ]]; then
                if [[ "$other_name" == cosmic-comp ]]; then other_name=cosmic; fi
                session_classify "$other_name"
                session_source='running compositor process (fallback)'
            fi
        fi
    fi
    return 0
}

print_detected_session() {
    printf 'Desktop: %s\n' "$session_desktop"
    printf 'Session type: %s\n' "$session_type"
    printf 'Compositor / window manager: %s\n' "$session_compositor"
    printf 'Detection: %s\n' "$session_source"
    case "$session_backend" in
        kde) printf 'Idle watcher backend: KDE (C++/KIdleTime)\n' ;;
        gnome) printf 'Idle watcher backend: GNOME (C/GLib/Mutter)\n' ;;
        *) printf 'Idle watcher backend: unsupported (no automatic idle integration available)\n' ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    detect_desktop_session
    print_detected_session
    if [[ "$session_backend" != kde && "$session_backend" != gnome ]]; then
        exit 2
    fi
fi
