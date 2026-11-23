# ASCII Saver V77 (0.77.0): preview layout and controls

Addresses **D01–D04** in the user-observed issues document. No speculative performance or stability work.

## What changed

- Both single-effect preview launchers pass `--anchor-canvas c` to the existing Rust renderer, so the ASCII canvas is centered in the available terminal grid and can be repositioned on terminal resizing. Text shapes, animation parameters, output colors and playback pacing are unchanged.
- Independent preview: a native libadwaita titlebar displays the effect name and provides **Replay**. The redundant in-content **Close preview** button and the explanation about mouse movement are removed. The window-manager close control still ends the renderer and frees the terminal. Replay re-runs the last effect with its recorded font and palette config.
- Pinned preview: increased height from 180 to 240–280 logical pixels, while maintaining a 320-pixel minimum scrolling effect gallery. Effect Library opens 100 px taller by default to make room.
- Effect Library: clicking an animated effect sample toggles its checkbox, matching Playlist Editor. The Play button remains a separate action.
- Removed repetitive preview help block and incidental explanatory text above the gallery.

## Verification and limitations

- Headless Python tests cover centered spawn arguments, Rust anchor implementation, Replay state, no extra close control, thumbnail selection without playback, and gallery height constraints.
- Installer, source syntax, source assets and ZIP integrity are checked for this release.
- **Not yet verified:** live GTK/VTE layout under GNOME/KDE Wayland, resize visuals while an effect is running, and Rust build/runtime on the target machine. The later device test should include narrow windows and mixed-font artwork.
