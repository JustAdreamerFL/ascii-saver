# ASCII Saver V82 (0.82.0): effect classifications and clear activation status

Date: 2026-11-07 (experimental source build, not runtime-verified).

## Changes

- Add small, consistent `Short · Gentle`-style metadata captions under every effect card in **both** Effect Library and Playlist Editor (user report D05). Captions use the existing qualitative grouping data; they are not performance measurements.
- In the Dashboard, separate saved **Automatic activation** status from the **Idle watcher** process status and from manual Start/Preview. The **Configure** action opens the existing Activation settings (report B212). It does not kill/start a service or silently save another open Preferences window.
- Introduce `TASKS.md` as the authoritative checked user-issue checklist. Correct V80 hot-plug's obsolete unchecked line in the old `UX-ROADMAP.md`. Keep historical reports intact.
- Add automated tests for qualitative captions, the statuses and UI wiring.
- Include `effect_metadata.py` in the installer payload.

## Testing and limitations

Verification: 381 Python tests passed and 1 was skipped (GTK/VTE unavailable). Installer tests, 37 preview packs, Python compilation and shell syntax checks passed. Automated tests exercise the metadata and dashboard status model, plus source-level GUI contracts. Actual GTK/VTE rendering and real KDE/GNOME window management are not validated in this environment. See `TASKS.md` for the remaining runtime checks.
