from __future__ import annotations

import json
from pathlib import Path

from pycmn import bib_locales


EXPECTED_ROW_COUNT = 77


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def book_abbreviation_from_verse(verse: str) -> str:
    parts = verse.split(" ", 1)
    if len(parts) != 2:
        raise ValueError(f"unexpected verse format: {verse!r}")
    return parts[0]


def expected_plus_files_by_book_abbreviation(table: dict[str, object]) -> dict[str, str]:
    verse_book_name_by_abbreviation = table.get("verse_book_name_by_abbreviation")
    if not isinstance(verse_book_name_by_abbreviation, dict):
        raise ValueError(
            "table JSON missing object key 'verse_book_name_by_abbreviation'"
        )

    expected: dict[str, str] = {}
    for abbreviation, std_book_name in verse_book_name_by_abbreviation.items():
        if not isinstance(abbreviation, str) or not isinstance(std_book_name, str):
            raise ValueError(
                "table.verse_book_name_by_abbreviation must map strings to strings"
            )
        try:
            bk24id = bib_locales.bk24id(std_book_name)
        except KeyError as exc:
            raise ValueError(
                f"unknown standard book name {std_book_name!r} for abbreviation {abbreviation!r}"
            ) from exc
        expected[abbreviation] = f"{bib_locales.ordered_short_dash_full_24(bk24id)}.json"

    return expected


def verify_table_words_in_mam_plus(
    table_json_path: Path,
    mam_parsed_path: Path,
) -> dict[str, object]:
    table_data = load_json(table_json_path)
    if not isinstance(table_data, dict):
        raise ValueError("table JSON root must be an object")

    table = table_data.get("table")
    if not isinstance(table, dict):
        raise ValueError("table JSON missing object key 'table'")

    rows = table.get("rows")
    if not isinstance(rows, list):
        raise ValueError("table JSON missing list key 'rows'")

    expected_plus_file_by_book_abbreviation = expected_plus_files_by_book_abbreviation(
        table
    )

    if len(rows) != EXPECTED_ROW_COUNT:
        raise ValueError(
            f"expected exactly {EXPECTED_ROW_COUNT} rows, found {len(rows)}; "
            "this repository is scoped to the current fixed dataset"
        )

    plus_dir = mam_parsed_path / "plus"
    plus_files = sorted(plus_dir.glob("*.json"))
    if not plus_files:
        raise ValueError(f"no plus JSON files found at: {plus_dir}")

    plus_text_by_name = {
        path.name: path.read_text(encoding="utf-8") for path in plus_files
    }

    row_reports: list[dict[str, object]] = []
    missing_any: list[dict[str, object]] = []
    missing_expected: list[dict[str, object]] = []

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"row must be object, got: {type(row)}")
        row_number = row.get("row_number")
        verse = row.get("verse")
        word = row.get("word")

        if not isinstance(row_number, int):
            raise ValueError(f"row has invalid row_number: {row!r}")
        if not isinstance(verse, str):
            raise ValueError(f"row has invalid verse at row {row_number}")
        if not isinstance(word, str):
            raise ValueError(f"row has invalid word at row {row_number}")

        hit_files = [
            file_name
            for file_name, file_text in plus_text_by_name.items()
            if word in file_text
        ]

        book_abbreviation = book_abbreviation_from_verse(verse)
        expected_file = expected_plus_file_by_book_abbreviation.get(book_abbreviation)
        if expected_file is None:
            raise ValueError(
                f"unmapped verse book abbreviation {book_abbreviation!r} at row {row_number}"
            )

        expected_text = plus_text_by_name.get(expected_file)
        if expected_text is None:
            raise ValueError(f"expected plus file missing: {expected_file}")

        found_in_any = len(hit_files) > 0
        found_in_expected = word in expected_text

        report_row = {
            "row_number": row_number,
            "verse": verse,
            "word": word,
            "expected_plus_file": expected_file,
            "found_in_any_plus_file": found_in_any,
            "found_in_expected_plus_file": found_in_expected,
            "hit_files": hit_files,
        }
        row_reports.append(report_row)

        if not found_in_any:
            missing_any.append(report_row)
        if not found_in_expected:
            missing_expected.append(report_row)

    summary = {
        "row_count": len(rows),
        "unique_word_count": len({row["word"] for row in rows if isinstance(row, dict) and "word" in row}),
        "missing_any_plus_count": len(missing_any),
        "missing_expected_plus_count": len(missing_expected),
    }

    return {
        "summary": summary,
        "rows": row_reports,
        "missing_any_plus": missing_any,
        "missing_expected_plus": missing_expected,
    }