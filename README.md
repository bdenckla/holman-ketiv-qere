# holman-ketiv-qere

Three bodies of work Daniel Holman has sent Ben Denckla, each extracted from its
source:

- **Suggested UXLC corrections** — his emails to the UXLC's editor, rendered to
  `gh-pages/uxlc_corrections.html`. See "Suggested UXLC corrections" below.
- **Ketiv/qere review** — `Review of Qere and Kethib readings in the Aleppo and
  Leningrad.docx`, rendered to `gh-pages/table_data_findings.html`. That is the
  original scope of this repo and everything from here to "Suggested UXLC
  corrections" is about it.
- **Suggested MAM corrections** — his emails proposing corrections to MAM itself,
  extracted to `docs-not-served/mam_suggestions.json` and rendered onto the **same
  page as the ketiv/qere review**, `gh-pages/table_data_findings.html`. See
  "Suggested MAM corrections" below.

**The three are distinct, and the repo's name covers only one of them.** Only the
review is about ketiv/qere; the UXLC corrections are addressed to a different text,
and the MAM suggestions are about meteg and accent placement. A reader arriving at
this repo from its name should not assume otherwise.

**Two of the three share one report, and a filter separates them.** Ben's decision,
2026-09-02: the ketiv/qere review and the MAM suggestions are both about MAM, so
they are shown together on `table_data_findings.html` with a "Suggestion kind"
filter group — `ketiv/qere`, `meteg`, `accent placement` — that partitions the
page, so either body can be read alone or both together without navigating. The
UXLC corrections keep their own report, being addressed to a different text.

`gh-pages/index.html` links to the two rendered reports.

**The code that does the extracting and rendering is not in this repo.** It lives in the
sibling `../MAM-basics`, under that repo's `py/`, and writes back into this one. Every command
below runs from `C:\Users\BenDe\GitRepos\MAM-basics` on that repo's interpreter, and every
module path below is spelled relative to this repo, so `../MAM-basics/py/hkq_cmn/foo.py` names
a file over there. [CLAUDE.md](CLAUDE.md) lists which entry point writes which files, and which
tracked artifacts no program regenerates.

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
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_extract_docx_and_render_table.py
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
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_just_render_table.py
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

- `../MAM-basics/py/hkq_cmn/verify_table_words_in_mam_plus.py`

This module is import-only and is called by the extractor.

## Search Scripts

Phenomenon-search scripts live in `../MAM-basics/py/` when they are useful to
reuse or adapt, and write their reports back here.

Current example:

- `../MAM-basics/py/main_search_holam_he_qere.py`
- `../MAM-basics/py/main_search_final_hiriq_verse_text.py`

This script traverses mpu (MAM-parsed-plus) qere readings directly, reports which hits come from
the first argument of `קו"כ-אם`, and compares the vowel-only-form hit set against
`../MAM-basics/out/mam-qere-words.json` as a sanity check.

The final-hiriq script is a narrower verse-text search used to confirm the
issue-67-style edge case. It reuses `verse_texts_by_location`, keeps CGJ and
joiners inside Hebrew tokens, strips accents plus meteg before matching, and
prints all final-hiriq hits along with the tokens from Tsefaniah 2:9.

Shared helpers for future ending-pattern searches live in:

- `../MAM-basics/py/hkq_cmn/qere_projection.py`
- `../MAM-basics/py/hkq_cmn/qere_ending_search.py`

Shared helpers for verse-text token searches live in:

- `../MAM-basics/py/hkq_cmn/hebrew_text_tokens.py`

To create another ending-pattern search, copy
`../MAM-basics/py/main_search_holam_he_qere.py` and change `SEARCH_SPEC`.

Run it from the MAM-basics repo root with:

```powershell
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_search_holam_he_qere.py
```

It writes its report to `out/holam_he_qere_report.json`, which is tracked.

## Suggested UXLC corrections

Daniel Holman emails Chris Kimball and Ben Denckla suggested corrections to the
UXLC, a book at a time. Those messages are the source. Two steps, because this
repo is public and a `.eml` file's headers carry the correspondents' addresses.

**Ingest**, when a new message arrives. The `.eml` files are **not** tracked;
they live in `.novc/eml/`, which `.gitignore` already covers:

```powershell
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_ingest_uxlc_emails.py
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

Two tables in `../MAM-basics/py/hkq_cmn/uxlc_attachment_notes.py` settle attachments
whose filename does not name their own case: `COMPANION_IMAGE_CASES` for an
image named after the word a case compares against rather than the case itself,
and `IMAGES_WITH_NO_CASE` for an image of a case its message never writes up,
which is not written out at all. Both raise on an entry no message has.
`doc/uxlc-email-count-disagreements.md` is why the second of those two tables
exists: it sets out, message by message, where a stated count, the cases written
up and the images attached disagree, and what is still open with Holman.

**Estimate**, when a new message arrives, after ingesting it. This step needs
the sibling `../UXLC-utils` clone, whose core XML and Leningrad Codex page index
it interpolates between; a fresh clone of this repo does not have it, which is
why the estimates are tracked rather than worked out at render time:

```powershell
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_estimate_uxlc_locations.py
```

That writes two files. `data/uxlc_atom_locations.json` holds one estimated
folio, column and line per case; the estimator is MAM-basics'
`uxlc_misc.my_uxlc_location`, which the estimate step now imports directly —
`py/uxlc_misc/` and `py/uxlc_lci/` were vendored copies of it here until
2026-08-18 — and it takes a (book, chapter, verse, atom) quad, so no word
matching is involved. `data/uxlc_standard_atoms.json` holds the UXLC's atom
number per case, which is what a card shows.

**Three numberings are in play, and no two of them agree everywhere.** Holman
counts a ketiv/qere pair as one atom and does not count a mid-verse samekh; the
UXLC counts every child element of the verse; `my_uxlc.read_all_books`, which
the estimator walks, drops the `<k>` and keeps every `<q>`. So the atom number
in `CaseRef` is neither of the other two, and `_atom_numbers` in
`../MAM-basics/py/main_estimate_uxlc_locations.py` resolves it to the verse
element it names and reports that element's place in each of the other counts —
one for the card to show, one for the estimator to be handed.
`../MAM-basics/py/hkq_cmn/uxlc_standard_atoms.py` sets out the evidence for what the
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
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_render_uxlc_corrections.py
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
the page `../MAM-basics/py/hkq_cmn/uxlc_change_records.py` names. That page is a flat
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
`../MAM-basics/py/hkq_cmn/uxlc_bracketed_corrections.py` holds those, one table entry
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

The folio was decoded from Holman's ordinal until then, and
`doc/holman-manuscript-citations.md` is why it no longer is: five of the 124
citations name a scan file whose own name says it cannot hold the case's verse,
`623_Amos_9.12b-Oba_20a` for Micah 1:14 being the plainest. That document names
the five, shows that they are the complete set, says which two of them the UXLC's
change list already holds a record for and with what folio, and gives the
commands to re-establish all of it.

Two labels are relabelled for display, in `DISPLAY_FIELD_LABELS` in
`../MAM-basics/py/py_render/uc_case_card.py`: Holman's "Corrected Text" is shown as "Suggested
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
sentence. `../MAM-basics/py/hkq_cmn/uxlc_holman_forms.py` reads both out so that every
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
`../MAM-basics/py/uxlc_comments/`, keyed by case reference. `all_comments.py` documents the
key format and the entry fields and is the aggregator; each contributor gets a
module beside it. A key matching no case raises, so a typo is loud.

## Suggested MAM corrections

Daniel Holman emails Avi Kadish and Ben Denckla suggested corrections to **MAM
itself** — a third body of his work, and neither of the two above. As of
2026-09-02 there are 34 cases from three messages, in two groups:

- **30 meteg cases**, Judges 1:7.21 through 2Chronicles 32:7.18, from the message
  of 2026-08-31. In 29 of them MAM has a meteg where he reports the Aleppo Codex
  has none; the thirtieth, Isaiah 23:12.11, runs the other way.
- **4 accent-placement cases** — Joshua 10:12.3, Judges 10:11.1, 2Kings 17:15.15
  and Zechariah 2:4.11 — from the messages of 2026-08-21 and 2026-08-27, which
  carry the same four and differ only in that the later one adds a recommendation
  per case. He compares against an edition he calls **"HUB"**, which is the
  **Jerusalem Crown** (כתר ירושלים) — Ben Denckla's identification, 2026-09-02.
  `comparison_source` keeps Holman's label verbatim and `comparison_edition`
  holds the name; `CLAUDE.md` says why the two are separate fields.

**Ingest**, when a new message arrives. The `.eml` files are **not** tracked; they
live in `.novc/eml-mam/`, a second mailbox distinct from the UXLC one:

```powershell
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_ingest_mam_suggestions.py
```

That writes `docs-not-served/mam_suggestions.json` and one page crop per case into
`gh-pages/mam_img/`. Both are tracked, so regenerating and reading the diff is the
test; there is no separate verifier.

**Render**, which is `main_extract_docx_and_render_table.py` — the same command that
renders the ketiv/qere review, because the two share a page:

```powershell
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_just_render_table.py
```

The suggestions extract is **required**, not optional: a missing file raises rather
than rendering a page quietly short of 34 records. Each suggestion becomes a card
with anchor `mam001`..`mam034` and reference label `M1`..`M34`, deliberately not of
the `row<N>` shape the review's cards use — the report's two pages carry a redirect
script that sends an unknown `row<N>` fragment to the other page, and a suggestion
is on one page only.

The kind a card gets is **derived** from Holman's two forms, not from which edition
he compares against: a case whose two forms become equal once every meteg is dropped
is a meteg case, and everything else is accent placement. Keying it to the edition
would give the same answer today, every meteg case being an Aleppo Codex comparison
and every accent-placement case a Jerusalem Crown one, and would silently mislabel
the first message that breaks that coincidence.

All 34 are on the Active page. The Suppressed page holds closed **issues**, and only
the review's rows have issues.

**The privacy boundary here is stricter than the UXLC one**, and `CLAUDE.md` states
it: no message body is tracked at all, and the ingest harvests nothing from the
threads around these messages, reading only what Holman sent. What that protects is
the **personal** side of Ben and Avi's correspondence. A substantive judgment about
the text is a different matter — it settles a suggestion, and Avi is cited for it by
name; see "When a suggestion is ruled on" below.

### When a suggestion is ruled on: it is suppressed, and the reason cites whoever ruled

A suggestion stays open until somebody rules on it. A ruling is written down in
`../MAM-basics/py/hkq_cmn/mam_suggestion_dispositions.py` — which case, what was
decided, why, by whom, on what date — and the ingest attaches it to the case, so
the tracked extract carries it and regenerating and reading the diff is the test.
A suppressed case keeps its card, its crop and its number and moves to the
**Suppressed** page beside the ketiv/qere rows whose issues are closed; suppression
says the suggestion has been ruled on, not that it was never made. Its card leads
with the ruling, because a reader who does not know a case is settled will take the
recommendation under it as still standing.

**One case is suppressed so far: M17, 2Kings 17:15.15** (Ben's decision, 2026-09-02).
MAM is right and the geresh is misplaced in the Jerusalem Crown. Seth (Avi) Kadish
established this on 2026-08-28: the geresh appears to have been erased in the
Leningrad Codex, and the UXLC has it that way, but even erased it stood over the כ
rather than over the final ו. He notes the same misplacement onto the final ו in BHS
and in Mechon Mamre, and reads the three editions sharing it as evidence that they
share a source. He added a note in MAM about the geresh in the Leningrad Codex
rather than moving the accent.

**M32, Judges 10:11.1, may belong in the same position and has not been suppressed.**
Avi ruled on it in the same message — MAM is correct, the accented syllable beginning
with the י — and his later note says that error too is shared by the Jerusalem Crown
and Mechon Mamre. It is left active because Ben asked for M17 and only M17.

### One line of Holman's has been corrected, and the correction is Ben's

Zechariah 2:4.11's recommendation as sent reads "Place Mereka on first syllable",
which is wrong twice: the mark is a munaḥ rather than a merkha, and MAM already has
it on the first syllable of זֵרוּ, the Jerusalem Crown having it on the second — so
the line describes MAM's existing state rather than the change toward that edition.
It looks carried down from the Judges 10:11 row, whose recommendation is worded
identically and where the mark genuinely is a merkha. The extract shows "Place Munaḥ
on second syllable" and keeps his wording under `recommendation_as_sent`, with the
corrector and the reason under `corrections`.

**Holman did not correct this himself**, and the record must not imply that he did.
Checked 2026-09-02 across the whole mailbox: the line occurs in exactly one message,
the one of 2026-08-27, in both its body and its workbook. The message of 2026-08-21
carries the same four cases with no recommendation column at all, so it neither
states nor corrects the line, and every other occurrence in the mailbox is the
2026-08-27 message quoted back inside a reply. There is no follow-up revising it.

`../MAM-basics/py/hkq_cmn/mam_suggestion_corrections.py` holds the table, one entry
per replacement, and raises both on an entry whose original is not the field's exact
current value and on an entry naming no case — so a reworded message cannot leave a
correction silently unapplied, and a stale entry cannot sit unnoticed. It is the same
shape as `uxlc_bracketed_corrections.py`, which does this for the UXLC corrections.

### Where the crops come from, which differs by message

The 30-case message attaches its crops as ordinary image parts whose filenames
restate the case, so each is matched to its case by name. The two HUB messages
attach no images at all: their crops are embedded **inside** the attached `.xlsx`,
named `image1.png`..`image4.png`, and the only thing that says which case each
belongs to is the drawing anchor recording the cell it sits in.
`../MAM-basics/py/hkq_cmn/xlsx_xml_utils.py` reads both the cells and those anchors,
with the standard library alone as the DOCX reader beside it does.

### What the corpus check says, and what it does not

The ingest looks every case up in the sibling `../MAM-parsed/plus/*.json` and records
the result per case under `mam_plus_check`, with totals under `mam_plus_verify`. It
never fails the run: an index that disagrees with the corpus is a fact to be read off
the extract, not a reason to refuse a message.

**The atom index is derived, not taken from Holman**, so the indices here are
consistent. Each case gives two spellings of one stretch of text, MAM's and the
comparison edition's; measured 2026-09-02 across all 34, the MAM spelling occurs
exactly once in its verse and exactly one atom inside it differs between the two
spellings. Those two facts name one atom and no other, so there is no ambiguity to
resolve and the ingest raises rather than guess if either stops holding. Atoms are
counted with maqaf-joined atoms separate.

31 of Holman's 34 indices agree with the derivation. **The other three have been
corrected**: 1Kings 7:24 (17 as sent, 16 derived), 2Samuel 15:37 (8 as sent, 9
derived) and Judges 1:7 (21 as sent, 20 derived), each out by one and not in a
consistent direction, all three of them the atom יְרוּשָׁלַ͏ִם. A corrected case keeps
what he sent under `atom_as_sent` and `ref_as_sent`.

The four maqaf compounds are **not** among the corrections, though a cruder check
reports them as disagreements: Holman quotes a whole compound while numbering one of
its atoms, and the atom he numbers is the one bearing the difference every time.

Two more cases looked out by one and were not: Judges 5:6.7 and Judges 5:11.13 were
casualties of a defect in `../MAM-basics/py/hkq_cmn/mam_plus_verse_data.py`, which
dropped the shirah spaces of the Song of Deborah and so fused the atoms on either side
of them. That was fixed on 2026-09-02, in the same pass that found it; the ketiv/qere
artifacts regenerate byte-identical across the fix, so nothing else here depended on
the defect.

`comparison_form_already_present` is a separate question asked of every case: whether
MAM already has the form he proposes. A non-zero count there dates the local corpus
rather than saying anything about Holman. It was zero on 2026-09-02, including for the
two cases corrected on Wikisource on 2026-08-28, because the local `MAM-parsed`
predates those edits.

## Tests

The tests moved to MAM-basics with the code they exercise, into that repo's
`py/tests/`, and run as part of its whole suite from its repo root:

```powershell
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_test.py
```

That runner is a `pytest.main()` wrapper and passes its arguments straight
through, so a focused subset is a `-k` selection rather than a flag of its own —
this repo's `--verify-table-words-in-mam-plus` and `--h-dot-below-nfc` have no
counterpart there:

```powershell
C:\Users\BenDe\GitRepos\MAM-basics\.venv\Scripts\python.exe C:\Users\BenDe\GitRepos\MAM-basics\py\main_test.py -k verify_table_words_in_mam_plus
```

There is no registry to keep in step any more: pytest discovers `py/tests/`
itself, so a new file named `test_*.py` or `*_test.py` runs on being added.

The NFC lint that ran here as `--h-dot-below-nfc` still covers this repo's
tracked files. It is one of seven scopes in MAM-basics'
`py/tests/test_h_dot_below_nfc.py` — three when `0890cb8` wrote this on 2026-08-18, four
when book-of-job's arrived on 2026-08-19 (`ef8e384` there), seven when the codex-index trio's
did on 2026-08-22 (`fe6cef2`); count the `_Scope(` entries rather than trust this sentence —
rooted at `hkq_paths.hkq_data_root()`, and
it reads every tracked file here outside `out/` and `gh-pages/`.
