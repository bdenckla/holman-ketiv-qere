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
nineteen auto-approve rules named this repo's interpreter and the scripts that went with it, plus
nine `git` / `where.exe` / `settings.json` rules worth nothing on their own (this sentence said
"nothing but this repo's interpreter and the scripts" until the 2026-08-22 review's follow-up;
`git show 15824d4:.vscode/settings.json` is the record). Do
not add a `.py` back, and do not go looking here for the code that produced a file you are reading.
Run everything below from `C:\Users\BenDe\GitRepos\MAM-basics`, on that repo's interpreter — the
`.venv` left here has nothing to run.

**Seven commands regenerate everything, and there is no one command that runs them all.** Each is
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
  a command of its own. **It also reads `docs-not-served/mam_suggestions.json`** and renders
  those 34 cases onto the same page — since 2026-09-02 the report carries both bodies of work,
  separated by a "Suggestion kind" filter group rather than by two pages. That file is
  required: a missing one raises rather than rendering a page short of its records.
- `main_ingest_uxlc_emails.py` — writes `emails/<key>.txt` and `emails/<key>.json`, and each
  attached PNG into `gh-pages/uxlc_img/`. Needs the untracked mailbox at `.novc/eml/`, so a fresh
  clone cannot run it; see the address boundary below.
- `main_estimate_uxlc_locations.py` — writes `data/uxlc_atom_locations.json` and
  `data/uxlc_standard_atoms.json`. Needs the sibling `../UXLC-utils` clone.
- `main_render_uxlc_corrections.py` — writes `gh-pages/uxlc_corrections.html`,
  `docs-not-served/uxlc_corrections.json`, and the `gh-pages/` copies of
  `assets/uxlc_corrections.css` and `assets/uxlc_corrections.js`. Needs only what is tracked here.
- `main_ingest_mam_suggestions.py` — writes `docs-not-served/mam_suggestions.json` and the page
  crops under `gh-pages/mam_img/`. Needs the untracked mailbox at `.novc/eml-mam/`, a **second**
  mailbox distinct from `main_ingest_uxlc_emails.py`'s `.novc/eml/`, so a fresh clone cannot run
  it either. Verification against `../MAM-parsed/plus/*.json` is part of the ingest. This is
  Holman's suggested corrections to **MAM**, which is a third body of his work beside the
  ketiv/qere review and the UXLC corrections; see the stricter privacy boundary below. It writes
  no HTML — the cards are rendered by the two commands above, which is why a change here is not
  visible on the page until one of them runs.
- `main_search_holam_he_qere.py` — writes `out/holam_he_qere_report.json`.
- `main_search_final_hiriq_verse_text.py` — writes `out/final_hiriq_verse_text_report.json`.

An eighth, `main_just_render_table.py`, re-renders the report pages from an existing
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

**`.novc/` stays here** — it is this repo's gitignored scratch directory, and both mailboxes the
ingest steps read live in it: `.novc/eml/` for the UXLC corrections and `.novc/eml-mam/` for the
MAM suggestions.

## This repo is public, so no address may reach a tracked file

The `.eml` files Holman sends carry his address, Chris Kimball's, Ben's, and the routing headers.
They are deliberately **not** tracked: they live in `.novc/eml/`, and
`../MAM-basics/py/main_ingest_uxlc_emails.py` writes an address-free derivative under `emails/`
that everything else reads. `uxlc_email_extract.redact_addresses` runs over each body as it is read — one of the
messages is a forward and quotes the original To and From lines in its body text — and
`_sender_display_name` raises rather than let a From header with no display name through.

Keep that boundary where it is. Do not track a `.eml`, do not reintroduce the recipients, and
before adding a field to the derivative, check what it would carry out of the mail headers.

### The MAM suggestions keep a STRICTER boundary, and it is not the one above

Ben's instruction, 2026-09-02, on the messages under `.novc/eml-mam/`: what becomes public is the
suggestions themselves. So `main_ingest_mam_suggestions.py` tracks **no message body at all** — a
reference, the two forms Holman compares, his one-line description, his recommendation where he
gives one, and the message's subject, date and sender display name. That is the whole of what the
ingest takes.

Do not extend the UXLC ingest's looser rule to these messages because the two ingests sit beside
each other. Tracking a redacted body would satisfy the address rule above and still break this one:
the threads around these messages are a discussion **between Ben and Avi** about Holman's
suggestions, and harvesting them wholesale is what may not happen.

**What the boundary protects is the PERSONAL correspondence, not every sentence**, and this
section said the stronger thing for a few hours before Ben narrowed it the same day. In his words:
what he did not want to leak is *"Avi's more personal comments about being too busy at the moment
to process some of these suggestions in a timely fashion, and things like that."* A **substantive
judgment about the text** is the opposite case — it is what settles a suggestion, and Ben asked
outright that Avi be **cited** for it by name.

The two are kept apart structurally. The ingest harvests nothing from those threads, because it
reads only messages Holman sent. A judgment that settles a case is written down **deliberately**,
one entry at a time, in `../MAM-basics/py/hkq_cmn/mam_suggestion_dispositions.py`, with the
person who reached it named and the date. Nothing about anyone's availability or circumstances
belongs in such an entry.

`hkq_cmn/mam_suggestion_extract.py` enforces this structurally rather than by redaction: a message
contributes only if `SUGGESTION_SENDER_NAME` sent it, and every other message in the mailbox is
skipped and named in the run summary, which goes to stdout and is not tracked. Of the ten messages
in the mailbox on 2026-09-02, three were Holman's and contributed all 34 cases; the other seven —
two of Avi's forwards and five replies — contributed nothing, one of those forwards quoting all 30
of Holman's cases verbatim without that mattering.

One consequence shaped how the comparison edition is named. The two workbook messages label it
**"HUB"** and nothing else, and the identification of what edition that names was made by a
correspondent in a reply — on the wrong side of this boundary. So it was not read out of the
mailbox: Ben settled it directly, on 2026-09-02, as the **Jerusalem Crown** (כתר ירושלים). That is
why `comparison_source` and `comparison_edition` are two fields rather than one — the first holds
Holman's label verbatim, the second Ben's identification — and why the mapping sits in a table in
`../MAM-basics/py/hkq_cmn/mam_suggestion_extract.py` with its provenance written beside it. A label
with no entry in that table raises. Prose says "Jerusalem Crown" and nothing else, and never
"Breuer's Jerusalem Crown": Breuer advised on it without detailed involvement, and Yosef Ofer did
the detailed work.

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
