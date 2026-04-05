from __future__ import annotations

import json
from pathlib import Path
import re

from pycmn import bib_locales


EXPECTED_ROW_COUNT = 77

VERSE_PATTERN = re.compile(
    r"^(?P<book_abbreviation>.*) (?P<chapter>\d+):(?P<verse>\d+)\.(?P<segment>\d+)$"
)


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def parse_table_verse(verse: str) -> tuple[str, int, int]:
    match = VERSE_PATTERN.fullmatch(verse)
    if match is None:
        raise ValueError(f"unexpected verse format: {verse!r}")
    return (
        match.group("book_abbreviation"),
        int(match.group("chapter")),
        int(match.group("verse")),
    )


def expected_plus_locations_by_book_abbreviation(
    table: dict[str, object],
) -> dict[str, tuple[str, int]]:
    verse_book_name_by_abbreviation = table.get("verse_book_name_by_abbreviation")
    if not isinstance(verse_book_name_by_abbreviation, dict):
        raise ValueError(
            "table JSON missing object key 'verse_book_name_by_abbreviation'"
        )

    expected: dict[str, tuple[str, int]] = {}
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

        bk39ids = bib_locales.bk39ids_of_bk24(bk24id)
        try:
            book39_index = bk39ids.index(std_book_name)
        except ValueError as exc:
            raise ValueError(
                f"standard book name {std_book_name!r} not found in bk24 {bk24id!r}"
            ) from exc

        expected[abbreviation] = (
            f"{bib_locales.ordered_short_dash_full_24(bk24id)}.json",
            book39_index,
        )

    return expected


def _collect_text_fragments(node: object, out_parts: list[str]) -> None:
    if isinstance(node, str):
        out_parts.append(node)
        return
    if isinstance(node, list):
        for item in node:
            _collect_text_fragments(item, out_parts)
        return
    if isinstance(node, dict):
        tmpl_params = node.get("tmpl_params")
        if isinstance(tmpl_params, dict):
            for value in tmpl_params.values():
                _collect_text_fragments(value, out_parts)


def _verse_texts_by_location(
    plus_json: object,
) -> dict[tuple[int, int, int], str]:
    if not isinstance(plus_json, dict):
        raise ValueError("plus JSON root must be an object")

    header = plus_json.get("header")
    if not isinstance(header, dict):
        raise ValueError("plus JSON missing object key 'header'")

    he_to_int = header.get("he_to_int")
    if not isinstance(he_to_int, dict):
        raise ValueError("plus JSON header missing object key 'he_to_int'")

    book39s = plus_json.get("book39s")
    if not isinstance(book39s, list):
        raise ValueError("plus JSON missing list key 'book39s'")

    out: dict[tuple[int, int, int], str] = {}
    for book39_index, book39 in enumerate(book39s):
        if not isinstance(book39, dict):
            raise ValueError(f"book39 entry must be object, got {type(book39)}")
        chapters = book39.get("chapters")
        if not isinstance(chapters, dict):
            raise ValueError("book39 entry missing object key 'chapters'")

        for he_chapter, verse_map in chapters.items():
            if not isinstance(he_chapter, str):
                raise ValueError(f"chapter key must be string, got {type(he_chapter)}")
            chapter_num = he_to_int.get(he_chapter)
            if not isinstance(chapter_num, int):
                raise ValueError(f"chapter {he_chapter!r} missing in header.he_to_int")
            if not isinstance(verse_map, dict):
                raise ValueError(f"chapter value must be object, got {type(verse_map)}")

            for he_verse, verse_payload in verse_map.items():
                if not isinstance(he_verse, str):
                    raise ValueError(f"verse key must be string, got {type(he_verse)}")
                if he_verse in ("0", "תתת"):
                    continue
                verse_num = he_to_int.get(he_verse)
                if not isinstance(verse_num, int):
                    raise ValueError(f"verse {he_verse!r} missing in header.he_to_int")

                text_parts: list[str] = []
                _collect_text_fragments(verse_payload, text_parts)
                out[(book39_index, chapter_num, verse_num)] = "".join(text_parts)

    return out


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

    expected_plus_location_by_book_abbreviation = (
        expected_plus_locations_by_book_abbreviation(table)
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

    plus_verse_texts_by_name = {
        path.name: _verse_texts_by_location(load_json(path)) for path in plus_files
    }
    plus_search_text_by_name = {
        file_name: "\n".join(verse_texts.values())
        for file_name, verse_texts in plus_verse_texts_by_name.items()
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
            for file_name, search_text in plus_search_text_by_name.items()
            if word in search_text
        ]

        book_abbreviation, chapter_num, verse_num = parse_table_verse(verse)
        expected_location = expected_plus_location_by_book_abbreviation.get(
            book_abbreviation
        )
        if expected_location is None:
            raise ValueError(
                f"unmapped verse book abbreviation {book_abbreviation!r} at row {row_number}"
            )

        expected_file, expected_book39_index = expected_location

        expected_verse_texts = plus_verse_texts_by_name.get(expected_file)
        if expected_verse_texts is None:
            raise ValueError(f"expected plus file missing: {expected_file}")

        expected_verse_text = expected_verse_texts.get(
            (expected_book39_index, chapter_num, verse_num)
        )
        if expected_verse_text is None:
            raise ValueError(
                "expected verse missing in plus data: "
                f"file={expected_file}, book39_index={expected_book39_index}, "
                f"chapter={chapter_num}, verse={verse_num}, row={row_number}"
            )

        found_in_any = len(hit_files) > 0
        found_in_expected = word in expected_verse_text

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