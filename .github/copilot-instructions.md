# Copilot Instructions

## Temporary Scripts

Put reusable Python scripts that should be tracked under `py/`.

When a throwaway Python script is needed for this repo, write it under `.novc/` and run it from there. Do not use `python -c` or temporary files outside the repo.

## UTF-8

This repo contains Hebrew text.

- Always pass `encoding="utf-8"` to `open()`.
- Always use `ensure_ascii=False` when writing JSON.
- Preserve Hebrew text and other meaningful Unicode characters.

## Data Extraction Style

- Prefer straightforward, fail-fast extraction scripts over defensive wrappers.
- Keep reusable extraction scripts under `py/`.
- Keep tracked source documents at the repo top level when they should live in the repo.
- Keep tracked outputs under `docs/`.
- Put extracted images under `docs/img/`.
- Keep scratch or inspection artifacts in `.novc/` only.

## Python File Size

- Prefer a soft limit of about 300 lines for any Python file.
- When a file grows beyond that, prefer splitting logic into focused helper modules.

## Project Scope

- Treat this project as intentionally narrow and mostly static.
- The current table dataset has 77 rows and is expected to remain the effective scope.
- Prefer simple, direct checks and scripts over general-purpose, highly configurable frameworks.

## Vendoring Policy

- When vendoring from neighboring repos (for example MAM-basics), vendor whole source files.
- Do not create or keep partial, hand-trimmed copies of vendored files.
- Preserve upstream file contents as-is unless a local patch is explicitly required, and keep local patches minimal and documented.

## Windows Shell Search Tools

- Do not assume `rg` (ripgrep) is available on PATH in this repo's shell sessions.
- For file discovery, use PowerShell-native commands such as `Get-ChildItem`.
- For text search, use PowerShell-native commands such as `Select-String`.
- If `rg` is ever considered, first verify availability with `Get-Command rg -ErrorAction SilentlyContinue` and only use it when present.

## Aleppo Codex Location Lookup

To find where a word appears in the Aleppo Codex (page, column, line) and generate a visual preview, use the script in the sibling `codex-index-aleppo` repo:

```
cd ../codex-index-aleppo/py && ../.venv/Scripts/python.exe main_find_word_in_aleppo_images.py <book> <c:v> <word>
```

- **`book`** — book name as used in the codex line-break labels, e.g. `Job`, `Deut`.
- **`c:v`** — chapter and verse, colon-separated (e.g. `38:31`).
- **`word`** — the Hebrew word to find (accents/vowels optional; stripped fallback is automatic).
- **`--wide`** — optional flag; extends horizontal margins to capture masorah parva notes.

The script must be run from the `../codex-index-aleppo/py/` directory so its relative imports resolve. It requires the `codex-index-aleppo` venv (which has PIL/Pillow); this repo's venv lacks PIL.

**Coverage:** Line-break data exists for 35 surviving Aleppo leaves covering Deut 28:17 through Prov 1:8 (pages 001r–018v and 270r–281v). For verses in that range, the script reports page, column, line number, and word index, and opens an HTML image preview in `.novc/`. For verses outside the line-break data, it falls back to `index-flat-annotated.json` and reports only the page ID.

**Console output fields (when line-break data is available):**
- **`Page`** — leaf ID (e.g. `270v`).
- **`Location: col N, line N, word N`** — column, line number (1–28), word position on the line.
- **`Match method`** — how the word was matched: `exact`, `stripped`, `maqaf-tail-stripped`, `maqaf-joined-exact`, or `maqaf-joined-stripped`.
- **`Line`** — all words on that line (right-to-left manuscript order).

Example — finding כִּימָ֥ה in Job 38:31:

```
cd ../codex-index-aleppo/py && ../.venv/Scripts/python.exe main_find_word_in_aleppo_images.py Job 38:31 "כִּימָ֥ה"
```

## Leningrad Codex Location Estimate

To estimate where a word appears in the Leningrad Codex (page, column, line), use the script in the sibling `codex-index-leningrad` repo:

```
cd ../codex-index-leningrad/UXLC-utils-sparse && ../../holman-ketiv-qere/.venv/Scripts/python.exe main_uxlc_estimate_atom_loc.py <book_id> <c:v> <word>
```

- **`book_id`** — UXLC book name, e.g. `Numbers`, `Genesis`, `Isaiah`. The full list is in `py/my_tanakh_book_names.py` (the `ALL_BOOK_IDS` tuple).
- **`c:v`** — chapter and verse, colon-separated (e.g. `20:26`).
- **`word`** — the Hebrew word to find. Tries exact match first, then stripped (no vowels/accents). Raises an error if ambiguous.

Example — finding אֶֽת in Numbers 20:26:

```
cd ../codex-index-leningrad/UXLC-utils-sparse && ../../holman-ketiv-qere/.venv/Scripts/python.exe main_uxlc_estimate_atom_loc.py Numbers 20:26 "אֶֽת־"
```

Output: `{'page': '088A', 'fline-guess': '37.8', 'line-guess': '10.8', 'column-guess': 2}`

The output fields:
- **`page`** — Leningrad Codex page ID (e.g. `088A`).
- **`column-guess`** — estimated column (1, 2, or 3).
- **`line-guess`** — estimated line within the column.
- **`fline-guess`** — "flat line" (line number counting across all three columns continuously).

Note: the script has no dependencies beyond the standard library, so it can use this project's venv. It must be run from the `../codex-index-leningrad/UXLC-utils-sparse/` directory so its relative `py.*` imports resolve.
