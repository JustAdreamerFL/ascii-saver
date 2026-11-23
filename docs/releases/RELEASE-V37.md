# V37: Instrumented renderer verification and cleanup

- Adds a **real executable smoke test** checking end-to-end CLI invocation, JSON output, effect identity, and frame counts in the instrumented Rust binary, across original and automatic engine dispatch.
- `./verify-build.sh` now runs that smoke test after the Cargo build, failing if the renderer contract is broken.
- Cleans unique `ttfx` report files on failed VTE launches and on application shutdown. Avoids accumulation of orphaned temporary files after errors.
- Static tests check that both spawn-failure branches dispose of reports and that the smoke test is integrated into the build verifier.

**Not verified here:** Cargo compilation, full GTK import and real KDE Wayland operation, because Rust and GTK are absent from this environment. This update does not implement universal time scaling or KScreenLocker integration.
