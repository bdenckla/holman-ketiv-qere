# CLAUDE.md

This repo holds two bodies of Daniel Holman's work: the ketiv/qere review extracted from a
tracked `.docx`, and the suggested UXLC corrections extracted from his emails. Both workflows,
their entry points, and the ketiv/qere review's fixed 77-row scope are in [README.md](README.md).

## This repo contains no Python. Its generators live in `../MAM-basics/py/`

holman-ketiv-qere is data and prose: `gh-pages/`, `emails/`, `docs-not-served/`, `out/`, `data/`,
`io/`, `assets/`, `doc/`, and the tracked review `.docx`. Everything under the first six of those
directories is generated, and **every generator lives in the sibling repo `../MAM-basics`**, which
writes back into this one. All 100 tracked `.py` files left on 2026-08-18, together with `py/`'s
five `_provenance.md` vendoring breadcrumbs, `py/.gitignore` and `.vscode/settings.json`, whose
auto-approve rules named nothing but this repo's interpreter and the scripts that went with it. Do
not add a `.py` back, and do not go looking here for the code that produced a file you are reading.
Run everything below from `C:\Users\BenDe\GitRepos\MAM-basics`, on that repo's interpreter — the
`.venv` left here has nothing to run.

**Six commands regenerate everything, and there is no one command that runs them all.** Each is
the only program that writes the files named beside it:

```powershell
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_extract_docx_and_render_table.py
```

- `main_extract_docx_and_render_table.py` — the ketiv/qere review. Reads the tracked
  `Review of Qere and Kethib readings in the Aleppo and Leningrad.docx`; writes
  `docs-not-served/table_data.json`, `docs-not-served/introduction.md`,
  `gh-pages/table_data_findings.html`, `gh-pages/table_data_findings_suppressed.html`, and the
  `gh-pages/` copies of `assets/table_data_findings.css` and `assets/table_data_findings.js`.
  Verification against the sibling `../MAM-parsed/plus/*.json` is part of extraction rather than
  a command of its own.
- `main_ingest_uxlc_emails.py` — writes `emails/<key>.txt` and `emails/<key>.json`, and each
  attached PNG into `gh-pages/uxlc_img/`. Needs the untracked mailbox at `.novc/eml/`, so a fresh
  clone cannot run it; see the address boundary below.
- `main_estimate_uxlc_locations.py` — writes `data/uxlc_atom_locations.json` and
  `data/uxlc_standard_atoms.json`. Needs the sibling `../UXLC-utils` clone.
- `main_render_uxlc_corrections.py` — writes `gh-pages/uxlc_corrections.html`,
  `docs-not-served/uxlc_corrections.json`, and the `gh-pages/` copies of
  `assets/uxlc_corrections.css` and `assets/uxlc_corrections.js`. Needs only what is tracked here.
- `main_search_holam_he_qere.py` — writes `out/holam_he_qere_report.json`.
- `main_search_final_hiriq_verse_text.py` — writes `out/final_hiriq_verse_text_report.json`.

A seventh, `main_just_render_table.py`, re-renders the report pages from an existing
`docs-not-served/table_data.json` without re-reading the `.docx`. It writes a subset of the first
command's output and is not needed for a full pass.

**77 rows is a fixed project scope, not a count of what happens to be there.**
`docs-not-served/table_data.json` is expected to hold exactly 77, and a regeneration that changes
the number is a failure rather than a finding.

**Not everything under the generated directories is generated at all.** 160 of the 335 tracked
artifacts here are untouched by a full six-command run, measured by mtime on 2026-08-18 and twice
before that: **154 images under `gh-pages/img/`**, `gh-pages/index.html`, the two
`gh-pages/JC3 The Biblical Text in the JC Edition #19-ז` pages, `gh-pages/woff2/Taamey_D.woff2`,
`docs-not-served/table_data_fields.md` and `io/table_row_github_issues.json`. Deleting any of the
160 in the belief that a rebuild brings it back will lose it. The 154 are untouched by design:
`hkq_cmn.extract_docx_xml_utils.export_images` is write-once and raises rather than overwrite an
image whose bytes differ, with three Aleppo crops named in `PRESERVED_EXTRACTED_IMAGE_PATHS`
exempted as manual replacements. `io/table_row_github_issues.json` has a writer of its own,
`main_just_render_table.py --update-issue-metadata`, which reads this repo's GitHub tracker.

**`.novc/` stays here** — it is this repo's gitignored scratch directory, and the mailbox the
ingest step reads lives in it.

## This repo is public, so no address may reach a tracked file

The `.eml` files Holman sends carry his address, Chris Kimball's, Ben's, and the routing headers.
They are deliberately **not** tracked: they live in `.novc/eml/`, and
`../MAM-basics/py/main_ingest_uxlc_emails.py` writes an address-free derivative under `emails/`
that everything else reads. `uxlc_email_extract.redact_addresses` runs over each body as it is read — one of the
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

The authored copies are the four files in `assets/`, and the generators copy them into
`gh-pages/`, so an edit made to a `gh-pages/` copy is lost at the next run.

## Locating a word in the manuscripts, from MAM-basics

Neither script lives here, and as of 2026-08-22 **both are MAM-basics'**, so run both with
MAM-basics' interpreter by absolute path. Each addresses the manuscript data it reads by
absolute path too, so neither needs a `cd`.

Aleppo Codex — page, column, line, plus an HTML image preview. Coverage is whatever
`codex-index-aleppo/line-breaks/` holds, which as of 2026-08-03 is 35 leaves, `001r`–`018v` and
`270r`–`281v`; for a verse outside those it falls back to the codex index and reports the page
ID alone. `--wide` widens the crop to take in masorah parva.

```bash
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_ac_find_word_in_images.py Job 38:31 "כִּימָ֥ה"
```

This one moved too, and later than the Leningrad script below. It was
`codex-index-aleppo/py/main_find_word_in_aleppo_images.py`, run from that repo's own venv, until
Phase 3 of `../MAM-basics/doc/PLAN-evacuate-python-from-codex-index-trio.md` on 2026-08-22; that
repo's venv went in the same plan's Phase 7 the same day, and codex-index-aleppo now holds the
page images and the line-break JSON and no code at all. The note that stood here until then —
that the Aleppo script needed Pillow, "which this repo's venv lacks", so each script wanted its
own repo's interpreter — is obsolete in both halves: MAM-basics' venv has Pillow, and there is no
second interpreter left to choose between.

Leningrad Codex — an *estimate* of page, column and line. This one moved first: it ran from
`codex-index-leningrad` until 2026-08-03, and is now in MAM-basics, reading `../UXLC-utils`.

```bash
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_uxlc_estimate_atom_loc.py Numbers 20:26 "אֶֽת־"
```

Both match the word exactly first, then stripped of vowels and accents, and both refuse to
guess when a word matches more than one position in the verse.
