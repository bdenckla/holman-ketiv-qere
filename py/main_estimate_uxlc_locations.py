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
    for case in cases:
        _require_prose_page(case)

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


def _require_prose_page(case: CorrectionCase) -> None:
    """Refuse a case in Psalms, Proverbs or Job, whose LC pages have two columns.

    ``page_and_guesses`` turns a flat line into a column by cutting the page
    into equal 27-line thirds, which is the three-column layout of the rest of
    the manuscript. On a two-column Sifrei Emet page that arithmetic reports a
    column that is not there, and it reports it silently. Every case Holman has
    sent so far is in a prose book, so this guard has never fired; it is here so
    that the first Psalms case raises rather than renders wrong.
    """
    if tbn.get_secid(case.ref.book) == tbn.SEC_SIF_EM:
        raise ValueError(
            f"{case.ref.key} is in the Sifrei Emet, whose Leningrad Codex pages "
            "have two columns, not the three my_uxlc_location.page_and_guesses "
            "assumes. Work out the column from its flat line before letting "
            "this case reach the page."
        )


def _estimate(uxlc, pbi, case: CorrectionCase) -> AtomLocation:
    ref = case.ref
    guess = my_uxlc_location.page_and_guesses(
        uxlc, pbi, (ref.book, ref.chapter, ref.verse, ref.atom)
    )
    return AtomLocation(
        folio=guess["page"],
        column=guess["column-guess"],
        line=float(guess["line-guess"]),
        flat_line=float(guess["fline-guess"]),
    )


if __name__ == "__main__":
    main()
