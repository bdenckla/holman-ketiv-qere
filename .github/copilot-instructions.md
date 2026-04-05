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
