# V32: Elapsed-time scaling (experimental)

`ttfx --frame-rate 60 --time-scale 0.5 matrix` scales the internal elapsed clock of wall-clock effects while keeping the configured frame pacing. It is **not** universal duration scaling: effects based on discrete frame counts are unaffected. The separate `--duration-factor` option still scales delays and hence output FPS. Virtual-clock parity runs are unchanged.

The Rust code requires compilation with Cargo on a working development host. No claims of successful Rust compilation or KDE runtime testing are made.
