from __future__ import annotations

import json
from pathlib import Path


EXPECTED_ROW_COUNT = 77

EXPECTED_PLUS_FILE_BY_BOOK_ABBREVIATION = {
    "Josh": "B1-Joshua.json",
    "Judg": "B2-Judges.json",
    "1Sa": "BA-Samuel.json",
    "2Sa": "BA-Samuel.json",
    "1Ki": "BC-Kings.json",
    "2Ki": "BC-Kings.json",
    "1Ch": "FC-Chronicles.json",
    "2Ch": "FC-Chronicles.json",
    "Isa": "C1-Isaiah.json",
    "Jer": "C2-Jeremiah.json",
    "Eze": "C3-Ezekiel.json",
    "Job": "D3-Job.json",
    "Prov": "D2-Proverbs.json",
    "Ps": "D1-Psalms.json",
    "Zeph": "CA-The-12-Minor-Prophets.json",
}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def book_abbreviation_from_verse(verse: str) -> str:
    parts = verse.split(" ", 1)
    if len(parts) != 2:
        raise ValueError(f"unexpected verse format: {verse!r}")
    return parts[0]


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
        expected_file = EXPECTED_PLUS_FILE_BY_BOOK_ABBREVIATION.get(book_abbreviation)
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