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
- Keep tracked source documents under `source/` when they should live in the repo.
- Keep tracked outputs under `docs/`.
- Put extracted images under `docs/img/`.
- Keep scratch or inspection artifacts in `.novc/` only.
