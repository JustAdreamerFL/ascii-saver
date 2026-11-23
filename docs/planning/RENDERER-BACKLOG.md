# KDE ASCII Saver — terminal effects / renderer backlog

These issues are separate from V53 UI usability work. Fix UI first, then test render behavior. They are observed on a KDE Plasma Wayland setup with two differently oriented monitors.

1. **Cursor flash at startup:** a terminal caret/block flashes in the upper-left before the first frame of a fullscreen screensaver effect (T01).
2. **Cursor visible after preview effect ends:** VTE displays a caret at the bottom after rendering finishes in a standalone preview; no caret during actual animation (T02). Renderer should keep final frame and hide text cursor before, during, and after animations.
3. **Per-monitor artwork scaling:** auto-fit should respect the configured independent/shared mode and NEVER fit if disabled. Test portrait vs landscape monitors and the first frame, after effects complete, and after preferences changes.
4. **Actual random playback:** with ordered playlists disabled, sequence/first effect appeared identical each start (Round 1 F02); verify seeding and scheduling behavior.
5. **Palette progression and final ANSI colors:** preserve effect-generated color in held final frame; verify interpolated palette transitions *between* effects, not during an effect.
6. **Persistent playlist preview:** distinguish persistent, resizable playlist preview from real screensaver exit-on-input (Round 1 A03).

Status: observations collected; runtime root causes not proven. UI priority first, renderer work later unless small isolated fixes can be verified.
