# Copilot Instructions

## Temporary Scripts

Put reusable Python scripts that should be tracked under `py/`.

When a throwaway Python script is needed that imports from `py/` modules (e.g. `python_modules`, `pycmn`), create it as `py/novc_bar.py` and run it from the repo root: `.venv\Scripts\python.exe py\novc_bar.py`. Files matching `novc_*.py` are gitignored via `py/.gitignore`. The `novc_` prefix sorts these files apart from tracked `main_*` scripts. Do not use `python -c` or temporary files outside the repo.

For PowerShell throwaway scripts and non-Python artifacts (commit messages, issue bodies, etc.), use `.novc/` as before. **Never write multi-line PowerShell scripts inline on the command line**. Write a `.ps1` file under `.novc/` and run it with `.\.novc\script.ps1`. Inline multi-line PowerShell causes quoting, escaping, and line-continuation problems just like `python -c`.

**Git commit messages** — write to a **uniquely-named** `.novc/` file and commit with `git commit -F .novc/commit_msg_<slug>.txt`. Never pass a multi-line or Hebrew-containing commit message as a `-m` string — the Windows shell will mangle it. Use a unique slug per commit (e.g. `commit_msg_add_hiriq_check.txt`) — a stale generic filename silently produces the wrong message.

## UTF-8

This repo contains Hebrew text.

- Always pass `encoding="utf-8"` to `open()`.
- Always use `ensure_ascii=False` when writing JSON.
- Preserve Hebrew text and other meaningful Unicode characters.
- Prefer writing non-ASCII output to a file rather than stdout/stderr. When a script genuinely must print Hebrew, reconfigure the streams at the top of `main()` — the Windows console defaults to cp1252 and will raise `UnicodeEncodeError` on any `print()` containing Hebrew:

```python
import sys

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ...
```

- Use `$env:PYTHONUTF8="1"` only for `.novc/` throwaway scripts where changing the code is not an option. (`PYTHONIOENCODING` is deprecated in favor of `PYTHONUTF8`.)

## Data Extraction Style

- Prefer straightforward, fail-fast extraction scripts over defensive wrappers.
- Keep reusable extraction scripts under `py/`.
- Keep tracked source documents at the repo top level when they should live in the repo.
- Keep tracked outputs under `docs/`.
- Put extracted images under `docs/img/`.
- Keep scratch or inspection artifacts in `.novc/` only.

## CSS Light/Dark Mode

For any authored HTML/CSS, always support both light and dark mode based on the user's OS preference. Use `color-scheme: light dark` on `:root` and the CSS `light-dark()` function for all color values. Do **not** use `@media (prefers-color-scheme: dark)` blocks.

Define all colors as CSS custom properties in `:root` so dark-mode adjustments are centralized there, not scattered through the rules:

```css
:root {
  color-scheme: light dark;
  --bg:      light-dark(#f7f6f2, #1e1c1a);
  --card-bg: light-dark(#ffffff, #272421);
  --border:  light-dark(#d9d3c9, #3d3836);
  --text:    light-dark(#2d2a27, #e8e4e0);
  --muted:   light-dark(#666059, #9a938c);
  --accent:  light-dark(#1f5f8b, #5ba3cb);
}
```

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

## Python Environment

Always use `.venv/` for Python work. **Never run bare `python`, `python3`, `pip`, or `pip3`** — always use the explicit venv path: `.venv\Scripts\python.exe` / `.venv\Scripts\pip.exe`.

## No `python -c`

**Never use `python -c`** for any reason — shell escaping of multi-line strings and Hebrew Unicode text is unreliable. Write a `py/novc_bar.py` file and run it from the repo root.

## Fail Fast — No Silent Error Smoothing

Do **not** write defensive code that swallows errors or returns `None` on unexpected conditions. Only catch exceptions when there is a concrete recovery strategy. These are batch pipelines; a crash with a clear traceback is the correct response.

## Dict Access Style

- `d[key]` — when the key is **required** (a `KeyError` is a bug you want immediately)
- `d.get(key)` — when the key is **genuinely optional** and `None` is meaningful
- `d.get(key, default)` — when the key is optional and there is a natural default

## JSON Lists: Prepend, Don't Append

When adding to a semantically unordered JSON array, **prepend** rather than append. Appending requires a two-line diff; prepending is a clean one-line diff.

## No Unsolicited Git Operations

Never run `git commit` or `git push` without explicit permission from the user. Staging and status checks are fine.

## Never Amend Commits

Never use `git commit --amend` or `git rebase` unless the user explicitly asks. Always make new commits.

## Don't Close Issues Prematurely

Never close a GitHub issue until work is both committed **and** pushed.

## Before Discarding Work

Before any destructive git operation (`git reset`, `git checkout -- .`, `git stash drop`, etc.), run `git status` and `git diff --stat` first. If there are uncommitted changes beyond the current experiment, alert the user and ask them to commit or stash before proceeding.

Before a series of experiments that might need to be thrown away, ask the user to commit the current clean state first so there is a safe baseline to return to.

After writing or editing any Python file, run black before committing. Format only files you changed:

```
.venv\Scripts\python.exe -m black py\python_modules\foo.py
```

## GitHub Repository Owner

The owner is **bdenckla**. Use this for GitHub MCP queries.

## Local Sibling Repositories

Most repos are cloned as siblings at `../repo-name`. Use relative paths when referencing other repos — do not hard-code absolute paths.

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

## Multi-Line Content — Write to `.novc/` Files

When the payload is inherently multi-line (a commit message, a GitHub issue/PR body, etc.), write it to a file in `.novc/` and reference the file. Do not pass multi-line content as a command argument — the Windows shell mangles it.

- **Git commit messages** — write to `.novc/commit_msg_<slug>.txt`, then `git commit -F .novc/commit_msg_<slug>.txt`
- **GitHub issue/PR bodies** — write to `.novc/issue_body.md` (or similar), then `gh issue create --body-file .novc/issue_body.md`

## Screenshots

When the user refers to "the most recent screenshot" or similar, this means the most recent file (by last-write time) in:

```
C:\Users\BenDe\OneDrive\Pictures\Screenshots
```

## Authorship Marking

When generating a new version-controlled file (Python script, Markdown doc, etc.), include an authorship comment as the **first line**:

- **Python:** `# Initially generated by GitHub Copilot.`
- **Markdown/HTML:** `<!-- Initially generated by GitHub Copilot. -->`

This does not apply to throwaway files in `.novc/`.

## Markdown Formatting

Do not use bare tildes (`~`) as an abbreviation for "approximately." Markdown renderers interpret text between two `~` characters as strikethrough. Instead, write out "approx." or "approximately," or escape the tilde (`\~`).

## Do Not Mention Private Repos in Public Repos

Some sibling repositories are private. Never reference a private repo by name in commits, code, documentation, or issue/PR text destined for a public repo.
