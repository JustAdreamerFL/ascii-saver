# V55: UI playback controls, build cache and tracking

This version adds persistent Cargo release cache, a Preview/Close Preview dashboard button replacing Stop, fixes repeated playlist effects in windowed preview, shuffles shared effects across rounds when not ordered, reserves reset-button width (no slider jump), shortens the save toast to Saved, unifies watcher/renderer status models, and makes monitor artwork chooser/Edit/Reset controls clearer. A watcher-memory PSS diagnostic, renderer post-start failure log in `~/.cache/kde-ascii-saver/renderer.log`, and backlog are included.

**Not verified in a real KDE GTK session.** Auto-fit crashes and palette rendering remain open investigations; see BACKLOG-V55.md.
