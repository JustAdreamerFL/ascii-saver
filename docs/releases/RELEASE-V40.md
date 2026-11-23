# V40: virtual-clock simulation-hold pacing

Fixed uneven output cadence in the reference Rust renderer when `--virtual-clock` and `--simulation-hold > 1` are used together with a positive FPS cap. The first output of each held group now uses the same pacing enforcement as the subsequent repeats.

Unchanged: unheld virtual clock, uncapped playback, parity frame dumps and optimized engine dispatch. This is source-level only: cargo/rustc and a live KDE session are unavailable in this environment.
