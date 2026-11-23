# KDE ASCII Saver V46: Usability and visual correctness

Release based on the first successful V45 build and detailed CachyOS dual-monitor test feedback.

## Changes

- Animated gallery GIF playback now explicitly decodes and advances frames with GdkPixbufAnimation, Gtk.Picture and Gdk.Texture. Each preview starts only while mapped and stops updating while unmapped. All 37 supplied GIFs were verified as changing across frames.
- Effect Library moved into a separate, reusable window. The main preferences page no longer includes the 37-row gallery.
- Visual playlist editor gains animated effect previews, using the same mapped-only widget.
- Persistent top action bar now groups Start Now, Preview, Stop, Performance History, Measured Durations and Save Preferences. A separate sticky banner appears when a preference changes and offers Save or Discard. Saving/discarding clears the pending-change state.
- Independent monitor settings are controlled through a single switch: individual FPS limits, artwork/colors, and optional synchronized effect order appear only when enabled. The global FPS/palette controls are hidden in independent mode to avoid duplicate settings. Unified mode saves one shared effect order.
- Fixed an independent-monitor palette bug: it previously saved a *single* color for each monitor, so cycling never advanced. The editor now provides and persists three palette colors per monitor.
- Finished artwork hold no longer clears the VTE screen or redraws plain text from `logo.txt`; it retains the actual renderer's last frame, location and ANSI color attributes until the next effect starts.
- Auto-fit artwork for independently configured monitors. A conservative per-window font reduction is computed from the actual terminal character grid; the saved global font preference is preserved. The preferences page displays per-monitor estimated character capacity and clipping warnings.
- Performance window's monitor drop-down is rebuilt only when the available monitor IDs change, avoiding the two-second selection reset. Y-axis numeric scale marks added to CPU (%), RAM (MiB), GPU (%) and output FPS plots. Monitor labels prefer display model to connector. Measurement table keeps grouping by actual effect ID. First successful duration reports are now shown provisionally without requiring three runs.
- Palette transitions default to one color per completed effect when enabled (`palette_steps=1`); existing saved multi-step transitions remain valid. Smooth intermediate transitions, when selected, happen only between effects. **Important:** VTE terminal foreground does not override ttfx effects' internally chosen RGB colors. Complete effect palette override remains unfinished.
- Installer now copies new gallery and artwork-fit modules, checks for GdkPixbuf, and preserves the existing staged installation rollback.

## Verified here

- 138 Python tests passed/discovered (one skipped due to unavailable GTK bindings), including new static-integrity and artwork-fit regression tests.
- Shell syntax, installer test suite and all 37 GIF files checked.
- The user successfully built and installed the predecessor V45 Rust engine and KF6 watcher on CachyOS.

## Not yet runtime-verified

- GTK gallery GIF animation, font adjustment and preferences window on a real KDE Wayland session; this build environment has no Python GTK `gi` bindings.
- Updated Rust engine wasn't changed in V46, so the compiler-tested V45 renderer source is retained.
- Universal animation timing and native KScreenLocker lock background are still unfinished.
- VTE terminal foreground color cannot recolor all effects' internal ANSI/RGB character colors.
