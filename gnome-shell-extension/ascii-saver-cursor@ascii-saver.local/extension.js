/**
 * Optional GNOME Shell cursor bridge for ASCII Saver. GNOME Shell 49+.
 *
 * Gtk's 'none' cursor is scoped to its Wayland surface. When a shell actor
 * owns pointer focus, only the compositor can hide that cursor. Watching a
 * D-Bus lease avoids a polling loop and automatically restores the pointer
 * if the renderer crashes or its bus connection disappears.
 *
 * This extension does not alter the lock screen, dock, or window stacking.
 */
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const FULLSCREEN_BUS_NAME = 'io.github.robbybobby77.AsciiSaver.Fullscreen';

export default class AsciiSaverCursor extends Extension {
    enable() {
        this._tracker = global.backend.get_cursor_tracker();
        this._ownerPresent = false;
        this._inhibited = false;
        this._lockPollId = 0;
        this._watchId = Gio.bus_watch_name(
            Gio.BusType.SESSION,
            FULLSCREEN_BUS_NAME,
            Gio.BusNameWatcherFlags.NONE,
            () => {
                this._ownerPresent = true;
                this._update();
                this._startLockGuard();
            },
            () => {
                this._ownerPresent = false;
                this._stopLockGuard();
                this._update();
            }
        );
    }

    _startLockGuard() {
        if (this._lockPollId)
            return;
        // Safety fallback: if screen locking races with the renderer's own
        // D-Bus lock notification, release the pointer even before it quits.
        this._lockPollId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 1, () => {
            this._update();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _stopLockGuard() {
        if (this._lockPollId) {
            GLib.Source.remove(this._lockPollId);
            this._lockPollId = 0;
        }
    }

    _update() {
        const locked = Main.screenShield?.locked ?? false;
        const shouldHide = this._ownerPresent && !locked;
        if (shouldHide && !this._inhibited) {
            this._tracker.inhibit_cursor_visibility();
            this._inhibited = true;
        } else if (!shouldHide && this._inhibited) {
            this._tracker.uninhibit_cursor_visibility();
            this._inhibited = false;
        }
    }

    disable() {
        if (this._watchId) {
            Gio.bus_unwatch_name(this._watchId);
            this._watchId = 0;
        }
        this._ownerPresent = false;
        this._stopLockGuard();
        this._update();
        this._tracker = null;
    }
}
