"""Estimate where each of Holman's atoms sits in the Leningrad Codex.

Run from repo root:
    .venv\\Scripts\\python.exe py/main_estimate_uxlc_locations.py

Writes the tracked data/uxlc_atom_locations.json, which the render step reads.
This step needs the sibling UXLC-utils clone, whose core XML and LC index the
estimator interpolates between; the render step needs only what is tracked, so
a fresh clone can render the page but not re-estimate it -- the same division
the .eml ingest step already draws.

The estimator itself is MAM-basics' uxlc_misc.my_uxlc_location, vendored into
py/uxlc_misc/ and py/uxlc_lci/ by py/main_update_vendored_files.py. It takes the
(book, chapter, verse, atom) quad CaseRef already holds, so no word matching is
involved and none of the CLI's ambiguity cases arise.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from mb_cmn import bib_locales as tbn
from python_modules.uxlc_atom_locations import AtomLocation, write_locations
from python_modules.uxlc_email_extract import CorrectionCase, read_emails
from uxlc_misc import my_uxlc_location

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EMAILS_DIR = REPO_ROOT / "emails"
DEFAULT_IMAGE_DIR = REPO_ROOT / "gh-pages" / "uxlc_img"
DEFAULT_DATA_DIR = REPO_ROOT / "data"

NOTE = (
    "Estimated column and line for each atom Holman's emails raise, from"
    " MAM-basics' uxlc_misc.my_uxlc_location over the UXLC core XML and LC"
    " page index in the sibling UXLC-utils. Written by"
    " py/main_estimate_uxlc_locations.py and read by the render step; folio is"
    " the LC leaf in the DDDA form the manuscript image URLs use, line counts"
    " down from the top of the named column, and flat_line counts down the"
    " whole page across all three columns."
)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emails-dir", type=Path, default=DEFAULT_EMAILS_DIR)
    parser.add_argument("--image-dir", type=Path, default=DEFAULT_IMAGE_DIR)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    _emails, cases = read_emails(args.emails_dir, args.image_dir)

    uxlc, pbi = my_uxlc_location.prep()
    locations = {case.ref.key: _estimate(uxlc, pbi, case) for case in cases}
    path = write_locations(args.data_dir, locations, note=NOTE)

    print(
        json.dumps(
            {
                "case_count": len(cases),
                "output_path": path.as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _columns_on_page(book: str) -> int:
    """How many columns a leaf of this book has, as the estimator counts them.

    The Sifrei Emet -- Psalms, Proverbs and Job -- are written two columns to a
    page and the rest of the manuscript three. This is the same rule
    ``my_uxlc_location._page_column_count`` applies when it works out how many
    flat lines a page holds, restated here because this module needs it to read
    the answer back.
    """
    return 2 if tbn.get_secid(book) == tbn.SEC_SIF_EM else 3


def _require_column_on_page(case: CorrectionCase, guess: dict) -> None:
    """Raise if the estimated column is not a column this book's leaves have.

    ``page_and_guesses`` cuts the flat line into 27-line columns, naming the
    third for anything past 55. Both directions of that arithmetic use the same
    27 lines per column, so the cut is right for a two-column Sifrei Emet leaf
    too, as long as the flat line stays on the leaf. What it cannot do is notice
    when the flat line runs off the bottom: on a Psalms page it would report a
    third column, which is not a column that page has.

    This replaces a guard that refused every Sifrei Emet case outright, on the
    ground that the three-column cut reported a column that was not there and
    reported it silently. Measured 2026-08-12 over the 63 Sifrei Emet cases in
    Holman's Psalms, Proverbs and Job messages, the largest flat line is 54.8
    (Job 34:20.4), so none of them reaches a third column; and the estimated
    column agrees with Holman's own stated column in 117 of the 124 cases, the
    seven that differ being split between prose books and the Sifrei Emet. So
    the failure that guard named is worth checking for rather than assuming,
    which is what this does.

    To re-establish those figures, compare the ``column`` written to
    ``data/uxlc_atom_locations.json`` against the ``Col. N`` in each case's
    manuscript citation in ``emails/``.
    """
    columns = _columns_on_page(case.ref.book)
    column = guess["column-guess"]
    if column > columns:
        raise ValueError(
            f"{case.ref.key} is estimated at column {column} of Leningrad Codex "
            f"folio {guess['page']}, from flat line {guess['fline-guess']}, but "
            f"a leaf of {case.ref.book} has {columns} columns. The estimate has "
            "run off the bottom of the leaf; work out what it should be before "
            "letting this case reach the page."
        )


def _estimate(uxlc, pbi, case: CorrectionCase) -> AtomLocation:
    ref = case.ref
    guess = my_uxlc_location.page_and_guesses(
        uxlc, pbi, (ref.book, ref.chapter, ref.verse, ref.atom)
    )
    _require_column_on_page(case, guess)
    return AtomLocation(
        folio=guess["page"],
        column=guess["column-guess"],
        line=float(guess["line-guess"]),
        flat_line=float(guess["fline-guess"]),
    )


if __name__ == "__main__":
    main()
