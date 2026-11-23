# ASCII Saver V78 (0.78.0): Diagnostics and artwork feedback

This release addresses two previously reported workflow problems, **C03** and **C02**, without adding unrelated renderer or stability changes.

## Diagnostics (C03)

- **Run Diagnostics** opens its own native libadwaita window instead of appending command output to the General preferences page.
- Individual installation checks appear as named PASS/FAIL rows with their details and an overall summary.
- **Run checks** repeats the read-only scan, **Copy results** copies a readable report, **Clear** removes results, and **Close** closes the window.
- The scan runs on a worker thread. Outdated results after Clear, reruns, or window closure are ignored.
- The existing `ascii-saverctl doctor` command is unchanged.

## Artwork editor (C02)

- The existing native text editor writes the artwork only when **Save** succeeds. It already uses an atomic file replacement.
- Closing with unsaved edits now requires an explicit **Discard** confirmation; choosing **Keep editing** returns to the editor.
- The Preferences window reports **Artwork saved**, **Closed without changes**, or **Unsaved edits discarded** only after the editor really closes. When a file was saved and then edited again before discarding, feedback distinguishes those two actions.
- The same behavior applies to the default artwork and per-display artwork files.

## Verification

- Headless regression suite including actual isolated editor close-handler behavior and atomic file-write failures.
- GTK/VTE live testing is still deferred; the above is code-complete but not yet visually verified in GNOME/KDE.
- Future work stays based on `PRIORITIES-V78.md` and the original user-observed backlog.
