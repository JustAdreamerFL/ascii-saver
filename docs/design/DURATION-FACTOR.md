# Experimental duration pacing (V30)

The modified Rust `ttfx` supports `--duration-factor 0.5..10.0` (default 1).
Factor 2 holds every simulation step twice as long, factor 0.5 halves its dwell.
Unlike a frame-skip implementation, **no simulation frames are omitted**.
It does not maintain independent constant output FPS: the output rate varies
with the duration factor. Some effects depend on wall-clock time and may not
scale linearly. Virtual-clock parity and unpaced mode are unchanged.

The KDE app accepts optional `duration_factor` in config.json, default 1.0.
No GUI slider is added until the engine is compile-tested.
