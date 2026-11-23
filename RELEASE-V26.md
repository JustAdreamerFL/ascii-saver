# Experimental V26: measured GPU activity graphs

This release adds a third, independently scaled five-minute performance graph for GPU engine busy time alongside CPU and RSS. It separates each monitor's process samples and does not manufacture 0% GPU utilization when DRM fdinfo counters are unavailable. GPU engine time is not whole-GPU utilization, and separate engine totals may exceed 100%.

A new pure-Python performance_series.py module handles filtering, sorting, invalid values and scale calculation. Seven tests cover the module. The installer now copies it to the application directory.

Still unfinished: Rust ttfx renderer modification, true presented/rendered FPS, duration scaling independent of FPS, GPU compositor attribution, and KDE lock screen integration. The GTK GUI and Plasma Wayland integration are not tested in this environment.
