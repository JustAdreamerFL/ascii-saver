# Experimental V23: verified spawn lifecycle telemetry

Effect start records are emitted only when VTE reports a positive child PID. Failed spawns produce `effect_spawn_failed` records. No changes to speed scaling or actual FPS measurement are claimed.

## Verification
- Python syntax compilation passed.
- Installer/uninstaller bash syntax passed.
- Four spawn-event regression tests passed.
- Complete suite: 80 tests discovered, one import error for unavailable `gi` (GTK), no assertion failures in the runnable tests.
- Not tested in a KDE Plasma Wayland session.

## Install
Back up `~/.config/kde-ascii-saver` before running `bash install.sh` from the extracted directory.
