# CLAUDE.md

This repo holds two bodies of Daniel Holman's work: the ketiv/qere review extracted from a
tracked `.docx`, and the suggested UXLC corrections extracted from his emails. Both workflows,
their entry points, and the ketiv/qere review's fixed 77-row scope are in [README.md](README.md).

## This repo is public, so no address may reach a tracked file

The `.eml` files Holman sends carry his address, Chris Kimball's, Ben's, and the routing headers.
They are deliberately **not** tracked: they live in `.novc/eml/`, and
`py/main_ingest_uxlc_emails.py` writes an address-free derivative under `emails/` that everything
else reads. `uxlc_email_extract.redact_addresses` runs over each body as it is read — one of the
messages is a forward and quotes the original To and From lines in its body text — and
`_sender_display_name` raises rather than let a From header with no display name through.

Keep that boundary where it is. Do not track a `.eml`, do not reintroduce the recipients, and
before adding a field to the derivative, check what it would carry out of the mail headers.

## Authored CSS uses `light-dark()`, not a `prefers-color-scheme` block

Every generated page supports both schemes off the reader's OS preference, and does it in one
place: `color-scheme: light dark` on `:root`, every colour a custom property whose value is a
`light-dark(<light>, <dark>)` pair. `gh-pages/table_data_findings.css` is the worked example.
Do not add an `@media (prefers-color-scheme: dark)` block — that scatters the dark values
through the rules instead of keeping them in the `:root` pairs where they can be read together.

## Vendor whole files

`py/main_update_vendored_files.py` copies from the neighbouring MAM-basics, and is the
authority on what it copies: the packages in `_VENDORED_PACKAGES` and the single files in
`_VENDORED_FILES`, each package's `_provenance.md` naming the MAM-basics commit it came
from. Copy a source file entire; do not keep a hand-trimmed subset of one, and keep any
local patch minimal and commented, so the next sync can tell a deliberate divergence from
drift.

A package is vendored by path intersection — the sync copies the files that already exist
locally — so adding a module means copying it in by hand once, after which the sync keeps
it current. A module that sits at the top of `py/` rather than inside a package cannot be
intersected that way, this repo's own `py/main_*.py` files being there and MAM-basics
having none of them, so those are named outright in `_VENDORED_FILES`.

## Locating a word in the manuscripts, from the sibling repos

Neither script lives here, and the Aleppo one needs Pillow, which this repo's venv lacks — so
run each with its own repo's interpreter.

Aleppo Codex — page, column, line, plus an HTML image preview. Coverage is whatever
`codex-index-aleppo/line-breaks/` holds, which as of 2026-08-03 is 35 leaves, `001r`–`018v` and
`270r`–`281v`; for a verse outside those it falls back to the codex index and reports the page
ID alone. `--wide` widens the crop to take in masorah parva.

```bash
cd C:\Users\BenDe\GitRepos\codex-index-aleppo
```

```bash
.venv/Scripts/python.exe py/main_find_word_in_aleppo_images.py Job 38:31 "כִּימָ֥ה"
```

Leningrad Codex — an *estimate* of page, column and line. This one moved: it ran from
`codex-index-leningrad` until 2026-08-03, and is now in MAM-basics, reading `../UXLC-utils`.

```bash
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_uxlc_estimate_atom_loc.py Numbers 20:26 "אֶֽת־"
```

Both match the word exactly first, then stripped of vowels and accents, and both refuse to
guess when a word matches more than one position in the verse.
