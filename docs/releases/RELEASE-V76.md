# ASCII Saver V76 (0.76.0): measured performance readability

This release addresses the user's reported performance-window and measurement
usability issues (C01/B210). No speculative CPU, renderer or stability changes.

## Changes

- Performance window now uses a **single vertically scrollable Adwaita page**.
  The old long, raw monospaced performance table has been replaced with native
  per-monitor `Adw.PreferencesGroup` rows. Shared GTK/VTE process overhead
  appears in its own separate group and is never summed into a monitor's child
  process. Data rows update without rebuilding the whole view every two seconds.
- The five-minute chart now has **four independently labeled vertical axes**:
  CPU (% of one logical core), resident RAM (MiB), DRM process-engine busy (%),
  and measured ttfx output FPS. Different monitors have distinct, labeled line
  colors. Shared overhead uses a dashed neutral line for clarity.
- Measured FPS appears as **individual completion-time dots**, not a fabricated
  continuous value between completed effects. Other plots break across gaps
  longer than 15 seconds, instead of interpolating through missing samples.
  A missing DRM counter is labeled unavailable, not as zero GPU utilization.
- The number breakdown shows per-effect averages, max RSS, measured FPS,
  configured FPS cap as a separate figure, and completed effect durations.
  Long descriptions can wrap and can be copied for bug reports.
- The pre-existing Measured Durations window keeps its monitor/preview filters
  and Adwaita rows, but now identifies **median** explicitly, gives the total
  number of recorded runs per monitor, and explains the relative duration
  classification and final-artwork-hold exclusion.
- Added an installable, pure-Python `performance_summary.py` model for safe
  aggregation and repeatable headless tests. Invalid/absent values remain
  unknown, and shared-process readings cannot inflate per-monitor data.

## Verification

- Python unit suite: 341 passed, 1 skipped (GTK/VTE unavailable).
- Added headless regression coverage for process isolation, missing values,
  measured FPS vs configured cap, duration filtering, chart contract and
  installation packaging.
- Installer, asset and syntax tests run before packaging.

## Not verified

No live GTK/VTE or Wayland session was available. The layout, wrapping, font
metrics, monitor model labels and actual chart repaint behavior require the
later user-device acceptance test. This is a source update, not a confirmed
runtime fix.
