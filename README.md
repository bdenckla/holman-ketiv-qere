# holman-ketiv-qere

Two bodies of work Daniel Holman has sent Ben Denckla, each extracted from its
source and rendered as a report under `gh-pages/`:

- **Suggested UXLC corrections** — his emails to the UXLC's editor, rendered to
  `gh-pages/uxlc_corrections.html`. See "Suggested UXLC corrections" below.
- **Ketiv/qere review** — `Review of Qere and Kethib readings in the Aleppo and
  Leningrad.docx`, rendered to `gh-pages/table_data_findings.html`. That is the
  original scope of this repo and everything from here to "Suggested UXLC
  corrections" is about it.

`gh-pages/index.html` links to both.

## Ketiv/qere review

This part of the repository tracks a focused extraction from:

- `Review of Qere and Kethib readings in the Aleppo and Leningrad.docx`

The extracted table is intentionally treated as a fixed project scope:

- We expect exactly 77 rows in `docs-not-served/table_data.json`.
- We do not expect the dataset to expand materially.
- Favor straightforward, fail-fast scripts over highly flexible tooling.

## Extraction Workflow

Run extraction with:

```powershell
.venv\Scripts\python.exe py/main_extract_docx_and_render_table.py
```

This also generates:

- `gh-pages/table_data_findings.html` (finding-based HTML report with summary counts and filtering)
- `gh-pages/table_data_findings_suppressed.html` (the same report for rows whose issue is closed)
- `gh-pages/table_data_findings.css` (report styles)
- `gh-pages/table_data_findings.js` (report filtering behavior)
- `docs-not-served/introduction.md` (extracted source introduction)
- `docs-not-served/table_data.json` (extracted source table data)

Checked-in issue metadata used by the findings report lives in:

- `io/table_row_github_issues.json`

To regenerate the HTML report from an existing JSON extract:

```powershell
.venv\Scripts\python.exe py/main_just_render_table.py
```

The extractor performs mpu (MAM-parsed-plus) verification as a mandatory part of extraction.
There is no separate standalone verifier command.

Default extraction behavior includes:

- Post-extraction verification against the live sibling `../MAM-parsed/plus/*.json`
- Verification summary embedded in `docs-not-served/table_data.json` under `mam_plus_verify`
- Finding-filterable report generated at `gh-pages/table_data_findings.html` with external `gh-pages/table_data_findings.css` and `gh-pages/table_data_findings.js`
- Fail-fast error if verification finds missing matches

## Verification Module

Verification logic lives in:

- `py/python_modules/verify_table_words_in_mam_plus.py`

This module is import-only and is called by the extractor.

## Search Scripts

Tracked phenomenon-search scripts live under `py/` when they are useful to
reuse or adapt.

Current example:

- `py/main_search_holam_he_qere.py`
- `py/main_search_final_hiriq_verse_text.py`

This script traverses mpu (MAM-parsed-plus) qere readings directly, reports which hits come from
the first argument of `קו"כ-אם`, and compares the vowel-only-form hit set against
`../MAM-basics/out/mam-qere-words.json` as a sanity check.

The final-hiriq script is a narrower verse-text search used to confirm the
issue-67-style edge case. It reuses `verse_texts_by_location`, keeps CGJ and
joiners inside Hebrew tokens, strips accents plus meteg before matching, and
prints all final-hiriq hits along with the tokens from Tsefaniah 2:9.

Shared helpers for future ending-pattern searches live in:

- `py/python_modules/qere_projection.py`
- `py/python_modules/qere_ending_search.py`

Shared helpers for verse-text token searches live in:

- `py/python_modules/hebrew_text_tokens.py`

To create another ending-pattern search, copy `py/main_search_holam_he_qere.py` and
change `SEARCH_SPEC`.

Run it from the repo root with:

```powershell
.venv\Scripts\python.exe py/main_search_holam_he_qere.py
```

It writes its report to `out/holam_he_qere_report.json`, which is tracked.

## Suggested UXLC corrections

Daniel Holman emails Chris Kimball and Ben Denckla suggested corrections to the
UXLC, a book at a time. Those messages are the source. Two steps, because this
repo is public and a `.eml` file's headers carry the correspondents' addresses.

**Ingest**, when a new message arrives. The `.eml` files are **not** tracked;
they live in `.novc/eml/`, which `.gitignore` already covers:

```powershell
.venv\Scripts\python.exe py/main_ingest_uxlc_emails.py
```

That writes the tracked derivative — per message, `emails/<key>.txt` (the body,
with every email address replaced by `[address removed]`) and
`emails/<key>.json` (subject, sender name, date, attachment list) — plus each
attached PNG into `gh-pages/uxlc_img/`.

**Render**, which needs only what is tracked, so a fresh clone can do it:

```powershell
.venv\Scripts\python.exe py/main_render_uxlc_corrections.py
```

That writes:

- `gh-pages/uxlc_corrections.html` (the report), plus its `.css` and `.js`
- `docs-not-served/uxlc_corrections.json` (the extract)

The report's pointed Hebrew is set in Taamey D, which the repo serves itself
from `gh-pages/woff2/Taamey_D.woff2` — a byte-for-byte copy of
`../hbofonts/gh-pages/woff2/Taamey_D.woff2`, the same copy the sibling repos
ship. Nothing regenerates it; replace it by hand from `hbofonts` when that repo
releases a new one.

The JSON is tracked so that regenerating and reading the diff is the test — a
message whose wording or structure parses differently cannot change the page
silently. There is no separate verifier.

To add a new message: drop the `.eml` into `.novc/eml/`, run the ingest step,
add the new cases to `SUGGESTION_KIND_BY_REF` in
`py/python_modules/uxlc_case_tags.py`, and run the render step. Everything else
is derived. The parser is fail-fast: an unrecognized field label, a heading
whose reference disagrees with its first field, an attachment naming a case that
is not in its message, two messages whose filenames reduce to one key, a case
with no classification, and a bidi formatting control the reader would never see
each raise rather than being dropped.

### Links to the UXLC's proposed changes

A card links the change items the UXLC's editor has entered for that word, at
the page `py/python_modules/uxlc_change_records.py` names. That page is a flat
chronological list whose anchors are dates and sequence numbers, so nothing in
an anchor says which verse a record is about and the case-to-record mapping is
written out in `CHANGE_RECORD_IDS_BY_REF` rather than derived. The module's
docstring records what the mapping is not free of: three cases the change list
numbers a different atom for, one case it splits into two records, and one
record that predates Holman's message. When a newer changes page supersedes that
one, update `CHANGES_PAGE_URL` and re-read the ids.

### What is Holman's and what is not

Every labelled line on a case card is Holman's, quoted from the message, with
two exceptions. The UXLC's note letter `c` sat inside a word of the Lev 25:20
case, wrapped in the bidi controls that kept it upright, and
`uxlc_email_extract._without_embedded_note_letter` drops it. And a word in
square brackets is Ben Denckla's, standing in for a word of Holman's:
`py/python_modules/uxlc_bracketed_corrections.py` holds those, one table entry
per replacement, and raises both on an entry whose original is not in the text
exactly once and on an entry naming no case, field or message. Either way the
tracked `emails/<key>.txt` and `emails/<key>.json` still hold the message as it
arrived, and the page's intro says what was changed.

The derived parts are the verse reference and atom index, the external links,
the change-item links, the Leningrad folio (decoded from the ordinal that begins
Holman's manuscript-image citation, and shown on that same line), and the one
editorial layer: the "What Holman asks for" classification in
`py/python_modules/uxlc_case_tags.py`.

**This repo is public, so no address reaches a tracked file.**
`uxlc_email_extract.redact_addresses` runs over each message body as the ingest
step reads it, and only the sender's display name is kept from the headers. The
cost of that choice: a fresh clone has the tracked bodies, JSON, HTML and PNGs
but cannot rerun the ingest step, which needs the mailbox.

### Commentary

Remarks on a case — Ben's, or ones arriving by email from others — live in
`py/uxlc_comments/`, keyed by case reference. `all_comments.py` documents the
key format and the entry fields and is the aggregator; each contributor gets a
module beside it. A key matching no case raises, so a typo is loud.

## Tests

Run all tracked tests from the repo root with:

```powershell
.venv\Scripts\python.exe py/main_test.py
```

`py/main_test.py --list` is the authority on which flags exist; the registry in
`TEST_MODULE_SPECS` is hand-maintained, so compare it against
`git ls-files "py/tests/test_*.py"` after adding a test file. Run a focused
subset with one of those flags:

```powershell
.venv\Scripts\python.exe py/main_test.py --verify-table-words-in-mam-plus
```

```powershell
.venv\Scripts\python.exe py/main_test.py --h-dot-below-nfc
```