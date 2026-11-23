# ASCII Saver V92 (0.92.0): Artwork Details and online art browsing

**Date:** 2026-11-08. Experimental/unreleased source build. Real network
access and GTK/GNOME/KDE/Wayland GUI operation remain unverified.

## Implemented

- **Local Details:** A single editor for tags, creator, description, source
  HTTPS link and license. Store only metadata in `artwork-meta/*.json`, never
  change the ASCII content. V90's V1 metadata loads unchanged; the first
  explicit save upgrades to V2, retaining all existing tags.
- **Browse Online:** Optional ascii-bin feed from
  `https://raw.githubusercontent.com/amwhoi/ascii-bin/main/asciiart_db.txt`.
  A single user action loads it in a nonblocking background worker.
  Filter by text, common tags and artwork shape; preview actual art with
  adaptive side-by-side/stacked layout. The external repository, not the app,
  owns the collection and updates it over time.
- **Safe Import:** A confirmation makes a **new** local `.txt` asset and an
  atomic source/rights sidecar. Never modify existing local artwork. Imported
  pieces remain fully editable with the standard Artwork Editor.
- **Offline:** Bounded cache at `online-cache/ascii-bin.txt`; failed refresh
  uses the last valid snapshot or displays a readable failure. The offline
  core and user-made art work even if this provider is unavailable.

## Licensing limitations

The repository labels its ASCII collection CC0, but its own `LICENSE-DATA`
acknowledges that it includes works authored by others, whose rights the
repository owner cannot waive. This is displayed to users and stored on
import as **CC0 claimed by collection; individual rights unverified**.
The original individual artist is recorded as **Unknown** unless identified
and substantiated separately. This is not a guarantee that every work is
free of third-party copyright or suitable for commercialization.
Source: https://github.com/amwhoi/ascii-bin/blob/main/LICENSE-DATA

## Security and lifecycle

- Strict HTTPS allowlisted feed and redirect check, maximum 3 MB raw feed;
  only text in the documented `===EOF===` format. Entries too large, too
  tall or too wide are skipped; terminal escape controls are removed.
- Cache and sidecars refuse symlinked targets/folders; atomic write and
  rollback for failed import provenance. No remote JavaScript or shell code.
- Network runs only on request and in a worker; user chooses imports.
  Closing the window prevents late worker updates.
- Existing renderer, old metadata/tag APIs and saved photo recipes remain
  compatible. New modules added to `install.sh`.

## Test scope

Headless tests cover parsing a representative ascii-bin fixture, malformed
feeds, cache/fallback, symlink rejection, import/attribution, duplicate-safe
saving, metadata migration and UI source wiring. The sandbox has no outbound
network/DNS or native GTK runtime, so actual remote fetch, UI layout and
Wayland integration are **not** reported as verified.

## Future

Provider extensions require independent source/rights validation; optional
publishing remains out of scope. Real GNOME/KDE tests still needed.
