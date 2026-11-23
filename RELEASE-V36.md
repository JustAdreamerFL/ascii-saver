# V36: measured output-FPS performance graphs

- Adds a fourth five-minute performance graph showing **measured ttfx active output FPS** per monitor, using completed `frame_stats` events.
- Adds a per-effect FPS summary and differentiates renderer output FPS from display-presented FPS and the configured FPS cap.
- Prevents frame statistics from being misinterpreted as CPU/RAM samples and excludes invalid measurements.
- Includes regression tests for monitor isolation, bad data and event filtering.

## Important limits

The modified ttfx Rust source remains uncompiled in this environment because Cargo is unavailable. The full KDE GTK/Wayland integration is not tested. FPS reports are generated on effect completion and are not continuous frame-by-frame telemetry. This package is experimental.
