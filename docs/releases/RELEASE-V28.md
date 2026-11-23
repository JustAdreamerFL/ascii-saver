# V28, measured active output FPS

Rust `ttfx` telemetry reports two different metrics:

- `average_output_fps`: frames written divided by overall effect wall time, including setup.
- `active_output_fps`: intervals between the first and last successfully written frames, excluding setup and teardown. Null if fewer than two frames are produced.

Reports use JSON schema 2; previously supported fields remain unchanged. Reports are written to a sibling temporary file and renamed at completion. The measurement is terminal-output FPS, not KWin presentation FPS.

This release does **not** implement independent duration scaling or complete lock-screen integration. Rust compilation and KDE runtime testing are still required.
