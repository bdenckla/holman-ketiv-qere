# holman-ketiv-qere

This repository tracks a focused extraction from:

- `Review of Qere and Kethib readings in the Aleppo and Leningrad.docx`

The extracted table is intentionally treated as a fixed project scope:

- We expect exactly 77 rows in `docs-not-served/table_data.json`.
- We do not expect the dataset to expand materially.
- Favor straightforward, fail-fast scripts over highly flexible tooling.

## Extraction Workflow

Run extraction with:

```powershell
python py/extract_docx.py
```

This also generates:

- `gh-pages/table_data_findings.html` (finding-based HTML report with summary counts and filtering)
- `gh-pages/table_data_findings.css` (report styles)
- `gh-pages/table_data_findings.js` (report filtering behavior)
- `docs-not-served/introduction.md` (extracted source introduction)
- `docs-not-served/table_data.json` (extracted source table data)

Checked-in issue metadata used by the findings report lives in:

- `io/table_row_github_issues.json`

To regenerate the HTML report from an existing JSON extract:

```powershell
python py/render_table_data_findings_html.py
```

The extractor performs MPP verification as a mandatory part of extraction.
There is no separate standalone verifier command.

Default extraction behavior includes:

- Post-extraction verification against `../MAM-parsed/plus/*.json`
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

- `py/search_holam_he_qere.py`
- `py/search_final_hiriq_verse_text.py`

This script traverses MPP qere readings directly, reports which hits come from
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

To create another ending-pattern search, copy `py/search_holam_he_qere.py` and
change `SEARCH_SPEC`.

Run it from the repo root with:

```powershell
python py/search_holam_he_qere.py
```

It writes its report to `.novc/holam_he_qere_report.json`.