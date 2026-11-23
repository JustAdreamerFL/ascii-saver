# V31 experimental

- Exposes Rust duration-factor in the GTK preferences, independent from the configured FPS multiplier control.
- Persists and validates duration_factor (0.5–10.0), default 1.0.
- Adds settings regression tests.

Important: duration-factor currently scales the engine's frame sleep period. It does **not** implement frame-independent simulation-time scaling and changes actual output FPS. Rust build/runtime still unverified in this environment.
