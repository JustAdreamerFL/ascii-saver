# V21: honest FPS instrumentation and playback traces

- Record selected effect, monitor, playback multiplier and effective `ttfx` FPS cap before each launch.
- Distinguish an FPS cap from actual rendered FPS. The latter remains unavailable.
- Show the most recent FPS cap per monitor/effect in the performance viewer.
- Exclude effect-start events from CPU/RAM aggregates.
- Continue retaining existing playback, playlists, activity protection, and installer.

This remains experimental; no real KDE Wayland runtime test was performed.
