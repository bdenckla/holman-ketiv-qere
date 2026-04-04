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

The extractor performs MPP verification as a mandatory part of extraction.
There is no separate standalone verifier command.

Default extraction behavior includes:

- Post-extraction verification against `../MAM-parsed/plus/*.json`
- Verification summary embedded in `docs/table_data.json` under `mam_plus_verify`
- Fail-fast error if verification finds missing matches

## Verification Module

Verification logic lives in:

- `py/python_modules/verify_table_words_in_mam_plus.py`

This module is import-only and is called by the extractor.