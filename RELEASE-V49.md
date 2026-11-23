# KDE ASCII Saver V49: Effect Library viewport and Playlist card behavior

## Addressed from real CachyOS V48 feedback

1. **Gallery collapse:** Moved search, duration/intensity filters and the result count *outside* the scrolling content; assigned the scrolling grid explicit vertical expansion, a minimum viewport height of 320 logical pixels and a homogeneous three-column layout. The gallery remains scrollable with or without a live renderer preview.
2. **Oversized live preview:** A single bounded-height VTE pane now appears **below** the gallery viewport. It does not replace the card area or take its available expansion. "Close preview" restores the full gallery height. The Play buttons still preview the selected effect using the user's actual artwork.
3. **Playlist effect selection:** Clicking an animated thumbnail toggles the corresponding effect, exactly like clicking the checkbox and effect name.
4. **Dedicated Playlist Play button:** Each playlist card has its own separate Play icon. It opens a non-modal renderer window rather than changing the selection. Closing that window stops its spawned renderer.
5. The low-memory preview packs and viewport activation from V47/V48 remain in place, without using runtime Glycin GIF decoding.

## Checks performed

- `python3 -m unittest discover -s tests -q`: 151 tests run, 1 skipped due to missing GTK system bindings.
- `bash tests/test_installers.sh`: passed (including install and uninstall integration stubs).
- Python compileall and shell syntax: passed.
- ZIP integrity and included preview packs: checked after packaging.

## Limitations

- This environment has no functional GTK/GDK/VTE desktop session, so the actual on-screen window geometry, animated thumbnails, and preview spawning must be checked in a running KDE Plasma session.
- No changes to the Rust `ttfx` engine; V45 compiled successfully on the user's CachyOS system.
- The precise height of a VTE preview may vary by font and GTK theme. The 180 logical-pixel scroller bounds its preferred height.

## Suggested desktop checks

1. Open Effect Library without selecting Play. Search, scroll to the bottom, resize the window and check that the cards fill the available viewport.
2. Click Play on a library effect. The card list should remain a usable scrolling area above a small preview pane. Click Close preview.
3. Open Playlist Editor. Click directly on an animation thumbnail: its checkbox should toggle. Click the separate triangle icon: a preview window should launch without toggling the checkbox. Close it and check for leftover `ttfx` processes.
