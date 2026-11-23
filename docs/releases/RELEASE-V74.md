# ASCII Saver V74 (0.74.0): contextual Save / Discard

Focus: user-reported issue E05 from `OBSERVATIONS-COMBINED.md` and
`UX-ROADMAP.md`, not speculative stability work.

## Changes

- Effect Library displays its own overlay **Save / Discard** banner for effect
  inclusion and its preview-mode choice. The banner does not reflow the
  scrolling cards, and it appears as soon as changes are made.
- Library Save writes only `exclude_effects` and `effect_preview_mode`. It
  updates exactly these fields in Preferences' saved baseline, leaving unsaved
  font, background, timing, artwork, playlist and monitor changes untouched.
  Library Discard rolls back only these two library-owned fields.
- When the library is the active window, its own Save/Discard controls are
  authoritative; the underlying Preferences banner is restored on focus return.
- Playlist Editor now shows a context-local, non-reflowing Save / Discard
  banner, rather than a permanently displayed header Save button. Generating,
  reordering, adding/removing playlists, editing details and toggling effects
  all update the dirty state; reverting edits makes the banner disappear.
  Discard restores a deep copy of the previously saved list.
- Closing the separate Playlist Editor **no longer reloads every Preferences
  control**. Only the playlist JSON is refreshed, and only if the user had not
  already edited that JSON in Preferences. Conflicting unsaved JSON edits stay
  visible with a warning; saved-file baseline is refreshed accurately.
- Added the GTK-independent `edit_state.py` model, installer staging and
  regression tests for isolated saves, failed writes, rollback and external
  editor conflicts.
- Added `PRIORITIES-V74.md` to distinguish old, addressed, outstanding and
  unverified reports before selecting the next task.

## Verification and limits

- Full Python test suite (including headless logic tests), shell installer
  syntax and asset integrity checks are expected before packaging.
- **No GTK4 / libadwaita runtime or Rust toolchain is available here.**
  Actual banner appearance, keyboard focus and KDE taskbar grouping remain
  untested until a live desktop check. Do not claim any runtime fix verified.
- Next user-observed P1 task: Playlist Editor gallery-first layout redesign.
