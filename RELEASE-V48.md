# KDE ASCII Saver V48: Gallery / Playlist usability and preview repair

## Fixes
- Corrects VTE `Terminal.spawn_async` call to use keyword parameters, as in the main renderer. Fixes the reproducible `Must be number, not cancellable` launch error.
- Displays the first thumbnail frame immediately, whether or not a card is actively animating. Full frame packs are opened only for visible cards. Keeps V47's viewport-limited playback, image-memory cleanup, and small preview assets.
- Puts Effect Library and Playlist Editor together under the sticky Actions toolbar, while keeping running/monitoring actions in the row above.
- Moves the playlist-mode switch into ordinary preferences, collapses raw playlist JSON under an advanced expander, removes large effect-group text and duplicate playlist button.
- Uses a GTK Overlay for the Save/Discard banner so showing it no longer shifts the toolbar, preferences or scrollbar.

## Limitations
- No GTK4/VTE desktop session or Rust compiler is available in the build container; needs a CachyOS runtime check.
- Individual rendered preview now appears in a collapsible panel above the scrolling Effect Library.
- Playlist editor is a separate window and its data are saved separately.
