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

Holman's messages through the Samuel one of 2026-08-08 carry his own plain text
beside the HTML, and `emails/<key>.txt` is that text verbatim. The seven from
Psalms Part I onwards have no plain-text part at all, so for those the tracked
body is `uxlc_email_extract._text_from_html`'s reading of the HTML: one line per
`<div>` or `<br>`, which is one line per line he typed, with the font markup
dropped.

Two tables in `py/python_modules/uxlc_attachment_notes.py` settle attachments
whose filename does not name their own case: `COMPANION_IMAGE_CASES` for an
image named after the word a case compares against rather than the case itself,
and `IMAGES_WITH_NO_CASE` for an image of a case its message never writes up,
which is not written out at all. Both raise on an entry no message has.

**Estimate**, when a new message arrives, after ingesting it. This step needs
the sibling `../UXLC-utils` clone, whose core XML and Leningrad Codex page index
it interpolates between; a fresh clone of this repo does not have it, which is
why the estimates are tracked rather than worked out at render time:

```powershell
.venv\Scripts\python.exe py/main_estimate_uxlc_locations.py
```

That writes two files. `data/uxlc_atom_locations.json` holds one estimated
folio, column and line per case; the estimator is MAM-basics'
`uxlc_misc.my_uxlc_location`, vendored into `py/uxlc_misc/` and `py/uxlc_lci/`,
and it takes a (book, chapter, verse, atom) quad, so no word matching is
involved. `data/uxlc_standard_atoms.json` holds the UXLC's atom number per case,
which is what a card shows.

**Three numberings are in play, and no two of them agree everywhere.** Holman
counts a ketiv/qere pair as one atom and does not count a mid-verse samekh; the
UXLC counts every child element of the verse; `my_uxlc.read_all_books`, which
the estimator walks, drops the `<k>` and keeps every `<q>`. So the atom number
in `CaseRef` is neither of the other two, and `_atom_numbers` in
`py/main_estimate_uxlc_locations.py` resolves it to the verse element it names
and reports that element's place in each of the other counts — one for the card
to show, one for the estimator to be handed.
`py/python_modules/uxlc_standard_atoms.py` sets out the evidence for what the
UXLC's numbering is, and how much weaker the samekh half of it is than the
ketiv/qere half. Of the 124 cases, 5 get a number on the card that is not the
one in Holman's email, and 1 changed the estimate it is worked out from.

Psalms, Proverbs and Job are written two columns to a Leningrad Codex leaf and
the rest of the manuscript three, and the estimator's flat-line arithmetic
already knows this — `my_uxlc_location._page_column_count` returns 2 for the
Sifrei Emet, so one of their pages is 54 flat lines rather than 81. What assumes
three columns is only the inverse, `page_and_guesses` cutting a flat line at
fixed 27-line boundaries; because both directions use the same 27 lines per
column, that cut is right for a two-column leaf too, so long as the flat line
stays on the leaf. `_require_column_on_page` checks exactly that, and replaced a
guard that refused every Sifrei Emet case outright. Measured 2026-08-12, the
largest flat line among the 63 Sifrei Emet cases is 54.8 (Job 34:20.4), so none
of them reaches a third column; and the estimated column agrees with Holman's
own in 117 of the 124 cases, the seven that differ being split between prose
books and the Sifrei Emet. To re-establish both figures, compare the `column`
and `flat_line` in `data/uxlc_atom_locations.json` against the `Col. N` in each
case's manuscript citation in `emails/`.

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

To add a new message: drop the `.eml` into `.novc/eml/`, then run the ingest,
estimate and render steps in that order. Everything else is derived. The
pipeline is fail-fast: an unrecognized field label, a heading whose reference
disagrees with its first field, an attachment naming a case that is not in its
message, two messages whose filenames reduce to one key, a case with no
manuscript-location estimate, a field label with no display rank, and a bidi
formatting control the reader would never see each raise rather than being
dropped.

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
the change-item links, and the manuscript location. That last one used to echo
Holman's citation; since 2026-08-11 the card reports an estimated column and
line from `data/uxlc_atom_locations.json` instead, gives his column beside it
wherever the two disagree, and does not show the scan-file name at all. Since
2026-08-12 the folio link is that file's estimate too, with Holman's decoded
ordinal named beside it where the two disagree, on the same footing as his
column. The citation is still in the tracked message body.

The folio was decoded from Holman's ordinal until then. What changed it:
measured 2026-08-12, five of the 124 citations name a scan file whose own name
says it cannot hold the case's verse, `623_Amos_9.12b-Oba_20a` for Micah 1:14
being the plainest. The five are Jer 3:24.2, Amos 8:12.8, Obad 1:1.17, Mic
1:14.10 and Zech 12:5.1, all in the message of 2026-08-12, four of them
consecutive in its MINOR PROPHETS section; their cited ordinals run low by 2 to
4 pages and the other 119 agree with the estimate exactly. To re-establish that,
parse the verse range out of the first token of each case's manuscript citation
in `emails/` and check it against the case's own reference.

Two labels are relabelled for display, in `DISPLAY_FIELD_LABELS` in
`py/py_render/uc_case_card.py`: Holman's "Corrected Text" is shown as "Suggested
Text" and his "Suggested Correction" as "Suggestion", the page saying
*suggestion* wherever it has the choice. The parser keeps his labels verbatim,
and so does the JSON extract. "Correction" stays where it names the UXLC's own
change items, and where it names Ben Denckla's bracketed correction of a word of
Holman's.

Nine cards carry one more derivation. Holman's Joshua, Judges and Samuel
messages state the word twice on lines of its own, "Current UXLC" or "Current
Text" and then "Corrected Text"; his Exodus, Leviticus and Deuteronomy messages
state neither, putting the form as it stands in parentheses on the "Word /
Verse" line and the form he proposes in parentheses inside his suggestion
sentence. `py/python_modules/uxlc_holman_forms.py` reads both out so that every
card reads alike, and the JSON extract records what it read under
`forms_read_from_prose`, so regenerating and reading the diff tests the reading.
Because that is a derivation over prose, every such case declares which of three
shapes its message has — `BOTH`, `CURRENT_ONLY` for the two that ask only for a
note, `PAIR_IN_FIRST_FIELD` for Deuteronomy 33:28, whose two forms are both on
the first line — and a mismatch raises. `require_full_coverage` raises on a case
missing from the table, on a case in it that has a "Corrected Text" line of its
own, and on a table entry naming no case.

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