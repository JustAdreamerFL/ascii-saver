# ASCII Saver V81 (0.81.0): single library preview control and release history

Addresses user-reported B214, the duplicated Effect Library Play mode between Preferences and Effect Library.

## Changes

- The **Play preview** selector is now visible only in Effect Library, where it applies. The Preview page in Preferences keeps navigation actions for Effect Library and Playlist Editor, without an empty duplicate Preview behavior group.
- The existing internal dropdown still mirrors the library selection to preserve snapshot/save semantics, V50-compatible `effect_preview_mode` configuration, library-local Save/Discard and live preview behavior. No renderer changes.
- Reordered the main CHANGELOG.md so experimental versions are listed newest first. Backfilled entries for releases with surviving `RELEASE-Vxx.md` notes instead of losing them in an unordered tail. No versions without release notes were invented.
- Added focused headless regression tests for visible control ownership, persistence wiring, changelog order and Python syntax.

## Verification and limitations

- Python unit tests: **374 passed, 1 skipped** because GTK/VTE is unavailable in this environment.
- Installer tests, Python source compilation, shell syntax and all **37 effect preview packs** passed validation.
- Actual GTK/Wayland visual behavior remains unverified until user testing is resumed.
