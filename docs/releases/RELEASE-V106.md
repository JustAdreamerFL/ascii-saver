# ASCII Saver V106 (0.106.0) - 2026-11-09

## Why this release

Based on live Fedora GNOME feedback: duplicate Close buttons, Preview grouped under a raw io.github... application, unchanged first palette color, and badly compressed narrow Preferences. Source-level fixes were made for all four reports; **live Wayland UI checks are still needed**, especially for the view reflow and taskbar grouping.

## Changes

1. **Modal dialogs:** Native `Adw.HeaderBar` already renders a close control. The redundant custom button has been removed. Escape still closes Help/System Information and fallback Keyboard Shortcuts.
2. **Preview identity:** Renderer and control interface now have the same app ID `io.github.robbybobby77.AsciiSaver`. Renderer is `Gio.ApplicationFlags.NON_UNIQUE`, allowing it to remain a separate GTK application process without D-Bus single-instance forwarding to Dashboard. Desktop entry/icon name match; real Alt-Tab/Dock/Task Manager grouping remains to be verified on GNOME and KDE.
3. **Palette progression:** New configurations cycle automatically through all three color swatches at each successful new effect rather than remaining on swatch one. V105 stored `cycle_palette: false` even when it was never explicitly chosen, so old configs without a `palette_mode` migrate to cycling. Saving Preferences in V106 writes `palette_mode: static` or `cycle`; after explicitly choosing Static it remains off. This is an intentional migration. A user with a deliberately static old palette must turn off **Cycle through palette colors** and save once. Fullscreen synchronization and independent preview counters are unchanged. Colors change **between effects**, not on every frame. Effect hold times may delay changes.
4. **Responsive Preferences:** Long labels, font/color selectors, spin controls and advanced timing controls are genuine adaptive `Adw.PreferencesRow`s, retaining single widgets and signals. At widths up to 620sp their controls stack under labels. Save/Discard is in a fixed-height bottom tray rather than over the first setting. The five-section dropdown remains available below 600sp.

## Tests performed here

- Python headless unittest suite including V106 palette migration, explicit static persistence and source contracts.
- Installer, session-detection, asset integrity, Python bytecode compilation, shell syntax.
- ZIP integrity and cumulative file check against V105.

## Limitations and suggested Fedora test

A GTK4/libadwaita/VTE runtime and a Wayland compositor are not available in the development container. This release **does not confirm** real GTK layout, exact Alt-Tab grouping or visually observed transitions. After installation and fully closing old GUI/Preview processes:

```sh
ascii-saver
ascii-saver preferences
ascii-saver preview
ascii-saver status
```

Test Help and System Information for a single Close button, then Esc. Open Preview with Dashboard closed and check its application association. Select visibly different swatches in Appearance, save and watch **two or more completed effects**. Turn cycle off, save, reopen and verify that a deliberately static choice persists. Resize Preferences through 900, 600, 450 and 350 logical pixels, especially Appearance and Animations with Advanced expanded. Report any clipping or missing controls.
