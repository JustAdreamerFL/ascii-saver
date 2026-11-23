# V38 experimental: frame-based simulation hold

A new `--simulation-hold N` (1..10) repeats each simulation frame N times at the output-frame cadence. This slows discrete-frame animations without skipping simulation steps, unlike modifying the FPS cap. N=1 is the original behavior. For N>1 the program uses the reference Rust engine rather than the optimized `fx` engine. The prior `--duration-factor` continues to affect output frame pacing, so set it to 1.0 when comparing modes.

Limitation: repeated frames increase output traffic, and actual terminal/compositor presented FPS is not guaranteed. Elapsed-time effects may still use wall time independently. Parity dump remains unchanged. No Rust compilation or KDE Wayland runtime validation in this environment.
