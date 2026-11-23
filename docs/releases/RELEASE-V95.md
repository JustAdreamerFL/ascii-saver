# ASCII Saver V95 (0.95.0): Online discovery UX

**Date:** 2026-11-08. Experimental cumulative source release. This is not a
confirmed GNOME/KDE desktop installation.

## User workflow

Open **Artwork Editor → My Artwork → Browse Online**. After the opt-in
collection loads, Search and the existing tag/shape filters still work, but the
list creates at most **48 cards** at a time. **Show More Artwork** appends the
next 48 cards without returning the list to the top or changing the selected
art. The result label reports the number shown, the number matching filters,
and the total number in the loaded collection.

**Sort** chooses original repository order, title A–Z, smallest/largest
character-cell area, or Shuffle. **Surprise Me** chooses a new random ordering
for the already loaded artworks, and automatically selects Shuffle. Sorting
and shuffling run locally, with no additional requests, account or download.
The collection has no reliable popularity and publication timestamps, so
sorting by Trending or Newest is intentionally not offered.

Refresh Online only allows one operation at a time. Imports are disabled during
a refresh, and errors keep the already shown in-memory gallery rather than
clearing it. On success, an active tag filter remains selected if it still
exists. A corrupted/unavailable network source still falls back to the bounded
on-disk cache through the existing V92 provider. Local artwork is independent.

## Data safety, licensing and scope

Import remains explicit and asks the user to acknowledge the warning that
ascii-bin's collection-wide CC0 claim **does not verify contributor rights**.
Metadata preserves repository provenance and an unverified individual-rights
note. No publishing, automatic imports or unsanctioned remote providers.
The text file is never changed merely by browsing, filtering or sorting.

## Verification and limitations

Run `python3 -m unittest discover -s tests -q`, installer/session checks,
`python3 -m compileall -q` and archive integrity checks. Automated tests cover
sort orders, deterministic shuffle, unmodified originals, paging boundaries,
filter + page combination, whitespace fidelity, GTK source wiring and
single-flight refresh. The public GitHub repository and expected text-feed
format were independently confirmed using web inspection on 2026-11-08.

**Not verified:** a direct HTTPS download from this build container (network
request failed), GTK/libadwaita window resizing or keyboard interactions on
GNOME/KDE, and rebuilding the Rust renderer without Cargo. Those remain open
runtime validation tasks, not a claim that the online integration is
fully field-tested.
