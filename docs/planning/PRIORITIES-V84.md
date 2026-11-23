# Current priorities after V84

Updated 2026-11-07. See [TASKS.md](../../TASKS.md) for the current checklist and [MASTER-BACKLOG.md](../../MASTER-BACKLOG.md) for every historically reported observation.

## Source improvements just completed

- **E02/B213**: group editor and library window identities with ASCII Saver by using application-owned windows, not a transient dialog and a separate GApplication. GTK-free lifecycle tests now cover reopening and child preview cleanup. **Runtime outcome is not verified.**

## Still requires real GNOME/KDE sessions

1. Verify KDE Task Manager shows both windows with ASCII Saver icon and groups them with Dashboard/Preferences; capture `app_id` and window relationships if it still fails.
2. Validate V74–V84 UI changes under GNOME/KDE, especially close/reopen behavior, Save/Discard, previews and fullscreen Escape/pointer dismissal.
3. Validate mixed portrait/landscape large-font auto-fit (~52pt), monitor hotplug, synchronization and independent palette progression.
4. GNOME cursor/dock behavior, especially with Shell extensions and lock/unlock.

## Deliberately deferred or awaiting evidence

No speculative CPU/RAM optimizer, KScreenLocker replacement, advanced inter-palette transitions, or new playlist modes. Keep the original user-approved scope and avoid half-complete features.
