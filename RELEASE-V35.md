# V35: stable effect identifiers in Rust FPS reports

Fixes a confirmed schema-contract bug: Rust telemetry previously serialized Debug
output (`Beams(BeamsConfig { ... })`) instead of the effect CLI key (`beams`).
KDE rejected such reports when it checked the expected effect name.

`EffectCommand::effect_name()` maps all 37 variants explicitly, keeping the
report format independent of debug representations and effect arguments.

Tested: static mapping tests, Python compilation and installer shell syntax.
Rust compilation and Plasma session tests remain outstanding here because Cargo
and KDE are unavailable in the build environment.
