# V25: DRM GPU engine-time measurement

Adds Linux DRM fdinfo per-process GPU engine busy-time sampling. This is NOT chip utilization and does not include KWin compositing or other processes. On unsupported drivers the field is unavailable. The GPU ratios of parallel engines may exceed 100% and must not be called whole-GPU usage.

Uses per-client deduplication, PID start-time reset protection and one-second samples. Adds a dedicated regression suite. True rendered FPS and duration rescaling still require renderer instrumentation.
