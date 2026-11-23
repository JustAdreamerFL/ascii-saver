# KDE ASCII Saver V50: Configurable Effect Library live preview

## What changed

- **Default: independent preview window.** Clicking Play in the Effect Library launches a single reusable, resizable `1100 × 660` GTK/VTE window. It is a regular window rather than the idle-triggered fullscreen screensaver: normal keyboard and mouse activity does not dismiss it. After an animation finishes, the window remains available until manually closed or used to play another effect.
- **Alternative: pinned library preview.** Choose the compact 180-logical-pixel terminal below the effect-card scroller. Its location is outside the scrolling grid so it remains visible as you scroll. Stop/Close Preview releases the terminal and sends SIGTERM to the renderer subprocess.
- **Easy switching.** The preview mode can be changed from Preferences (`Effect Library Play opens`) or directly inside Effect Library (`Play preview:`). Both selections synchronize. Save Preferences persists the choice to `config.json` as `effect_preview_mode`: `window` / `inline`; default is `window`. Changing back to a saved value clears the unsaved-changes banner.
- **Lifecycle.** The independent preview belongs to the main settings window and remains alive when the library gallery is closed. Only one renderer process per preview mode is used. Switching modes when playing another effect stops the old mode's renderer. Dedicated preview and screensaver idle activation remain separate.
- **No change to the Rust renderer or library thumbnail format.** Preview GIFs are still the compact image packs from V47 onward, so the historical Glycin memory issue is not reintroduced.

## Verification

- `python3 -m unittest discover -s tests -q`: 157 tests run, 1 skipped because the test runtime has no GTK libraries.
- `bash tests/test_installers.sh`: passed.
- `python3 scripts/check-release-assets.py`: passed for all 37 preview packs and installer payloads.
- `bash -n install.sh uninstall.sh`: passed.
- No live GTK, KDE Wayland or VTE integration testing was possible in this environment. Preview window input behavior and placement must be confirmed in a running Plasma session.

## Suggested desktop test

1. Open preferences and Effect Library, leave `Play preview` on **Large separate window** and click Play on any card. Move the pointer and type a harmless key. The new window should remain open; close the Effect Library and verify the preview stays visible. Close the preview using its own button.
2. Change the library mode to **Pinned below effect cards**, then click Play. Scroll the effect list and confirm the preview remains visible below it, without collapsing the grid.
3. Save Preferences, close and reopen settings. Confirm the selected mode is remembered. Switch modes and back to the saved value to confirm the unsaved banner disappears.
4. After closing each preview, check for residual `ttfx` processes.
