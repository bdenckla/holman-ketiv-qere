# holman-ketiv-qere

This repository tracks a focused extraction from:

- `Review of Qere and Kethib readings in the Aleppo and Leningrad.docx`

The extracted table is intentionally treated as a fixed project scope:

- We expect exactly 77 rows in `docs/table_data.json`.
- We do not expect the dataset to expand materially.
- Favor straightforward, fail-fast scripts over highly flexible tooling.

## Extraction Workflow

Run extraction with:

```powershell
python py/extract_docx.py
```

This also generates:

- `docs/table_data_findings.html` (finding-based HTML report with summary counts and filtering)
- `docs/table_data_findings.css` (report styles)
- `docs/table_data_findings.js` (report filtering behavior)

To regenerate the HTML report from an existing JSON extract:

```powershell
python py/render_table_data_findings_html.py
```

The extractor performs MPP verification as a mandatory part of extraction.
There is no separate standalone verifier command.

Default extraction behavior includes:

- Post-extraction verification against `../MAM-parsed/plus/*.json`
- Verification summary embedded in `docs/table_data.json` under `mam_plus_verify`
- Finding-filterable report generated at `docs/table_data_findings.html` with external `docs/table_data_findings.css` and `docs/table_data_findings.js`
- Fail-fast error if verification finds missing matches

## Verification Module

Verification logic lives in:

- `py/python_modules/verify_table_words_in_mam_plus.py`

This module is import-only and is called by the extractor.