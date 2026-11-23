# V29: FPS telemetry integration fix

The ttfx Rust schema-2 reports are now accepted by the KDE application (the previous V28 reader only accepted schema 1). Active output FPS is recorded separately from lifetime-average output FPS. Schema-1 reports remain supported. Corrupt, failed, and effect-mismatched reports are rejected. The new parser is installed with the application.

These figures measure terminal frames written, not compositor-presented frames. Rust compilation and KDE Wayland tests remain unverified in this environment.
