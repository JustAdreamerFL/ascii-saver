# V24 experimental: shared GTK/VTE process telemetry

Records the screensaver host process CPU and RSS separately from each monitor's ttfx subprocess. The GUI shows shared overhead separately and warns that summed RSS is not de-duplicated memory consumption. GPU percentage and real frames per second remain unavailable. This source is not validated on live Plasma Wayland.

## Verification

Unit tests plus Python compilation and shell syntax checks. No runtime GPU or Wayland testing performed.
