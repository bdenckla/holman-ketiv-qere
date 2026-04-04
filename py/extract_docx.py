from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import zipfile
from pathlib import Path
from typing import cast
from xml.etree import ElementTree as ET

from pycmn import bib_locales
from python_modules.verify_table_words_in_mam_plus import verify_table_words_in_mam_plus


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

CONTROL_CHARS = {
    "\u00a0": " ",
}

VERSE_PATTERN = re.compile(r"^(?P<book_abbreviation>.*) (?P<chapter>\d+):(?P<verse>\d+)\.(?P<segment>\d+)$")

STANDARD_BOOK_NAME_BY_ABBREVIATION = {
    "1Ch": bib_locales.BK_FST_CHR,
    "1Ki": bib_locales.BK_FST_KGS,
    "1Sa": bib_locales.BK_FST_SAM,
    "2Ch": bib_locales.BK_SND_CHR,
    "2Ki": bib_locales.BK_SND_KGS,
    "2Sa": bib_locales.BK_SND_SAM,
    "Eze": bib_locales.BK_EZEKIEL,
    "Isa": bib_locales.BK_ISAIAH,
    "Jer": bib_locales.BK_JEREM,
    "Job": bib_locales.BK_JOB,
    "Josh": bib_locales.BK_JOSHUA,
    "Judg": bib_locales.BK_JUDGES,
    "Prov": bib_locales.BK_PROV,
    "Ps": bib_locales.BK_PSALMS,
    "Zeph": bib_locales.BK_TSEF,
}

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCX_PATH = REPO_ROOT / "Review of Qere and Kethib readings in the Aleppo and Leningrad.docx"
DEFAULT_MAM_PARSED_PATH = REPO_ROOT.parent / "MAM-parsed"

NOTES_JUNK_REPLACEMENTS = (
    ("y\u202c\u200f", ""),
    ("\u202c\u202c", ""),
)

# Strip known invisible format marks before pattern counting.
INVISIBLE_MARK_PATTERN = re.compile(r"[\u034F\u200C-\u200F\u202A-\u202E\u2066-\u2069]")
HEBREW_RUN_PATTERN = re.compile(r"[\u0590-\u05FF\uFB1D-\uFB4F]+")
NOTES_PREFIX = "MAM - No Comments | UXLC - "
HAKETER_SEPARATOR = " | HaKeter - "
UXLC_YATIR_PATTERN = re.compile(r"^(?P<uxlc>.*)\n\((?P<yatir>[^)]+)\)$", re.DOTALL)

NOTES_TARGETED_FIXES_BY_ROW_NUMBER = {
    37: {
        "original": "MAM - No Comments | UXLC - מַה־לִּי־פֹה֙ מי־לי־",
        "fixed": "MAM - No Comments | UXLC - לי־ מַה־לִּי־פֹה֙",
    },
}

ALLOWED_LENINGRAD_TEXT_VALUES = {"", "’"}


def normalize_text(text: str) -> str:
    for old, new in CONTROL_CHARS.items():
        text = text.replace(old, new)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def paragraph_text(paragraph: ET.Element) -> str:
    texts = [node.text or "" for node in paragraph.findall(".//w:t", NS)]
    return normalize_text("".join(texts))


def cell_payload(cell: ET.Element, rel_map: dict[str, str]) -> dict[str, object]:
    parts = []
    for para in cell.findall("./w:p", NS):
        text = paragraph_text(para)
        if text:
            parts.append(text)

    image_targets = []
    for blip in cell.findall(".//a:blip", NS):
        rel_id = blip.attrib.get(f"{{{NS['r']}}}embed")
        if rel_id is not None:
            image_targets.append(rel_map[rel_id])

    return {
        "text": "\n".join(parts),
        "image_targets": image_targets,
    }


def slugify(label: str) -> str:
    text = label.strip().lower()
    text = re.sub(r"[^0-9a-z]+", "_", text)
    return text.strip("_") or "entry"


def verse_book_abbreviation(verse: str) -> str:
    match = VERSE_PATTERN.fullmatch(verse)
    if match is None:
        raise ValueError(f"unexpected verse format: {verse!r}")
    return match.group("book_abbreviation")


def standard_book_name(book_abbreviation: str) -> str:
    try:
        return STANDARD_BOOK_NAME_BY_ABBREVIATION[book_abbreviation]
    except KeyError as exc:
        raise ValueError(f"unknown book abbreviation: {book_abbreviation!r}") from exc


def intro_markdown(paragraphs: list[str]) -> str:
    if not paragraphs:
        return ""

    title = paragraphs[0]
    body = paragraphs[1:]
    lines = [f"# {title}", ""]
    bullet_mode = False
    for paragraph in body:
        if paragraph == "Breakdown of the 77 Readings:":
            lines.append("## Breakdown of the 77 Readings")
            lines.append("")
            bullet_mode = True
            continue

        if bullet_mode and re.match(r"^[0-9]+ Instances?:", paragraph):
            lines.append(f"- {paragraph}")
            continue

        if paragraph == "Sincerely,":
            bullet_mode = False
            if lines and lines[-1] != "":
                lines.append("")

        lines.append(paragraph)
        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def export_images(
    archive: zipfile.ZipFile,
    row_number: int,
    column_key: str,
    targets: list[str],
    image_dir: Path,
) -> list[str]:
    exported_paths = []
    for image_index, target in enumerate(targets, start=1):
        extension = Path(target).suffix or ".bin"
        filename = f"row{row_number:03d}_{column_key}_{image_index:02d}{extension}"
        output_path = image_dir / filename
        output_path.write_bytes(archive.read(f"word/{target}"))
        exported_paths.append(output_path.as_posix())
    return exported_paths


def strip_known_notes_junk(notes: str) -> str:
    for old, new in NOTES_JUNK_REPLACEMENTS:
        notes = notes.replace(old, new)
    return notes


def abstract_hebrew_runs(text: str) -> str:
    return HEBREW_RUN_PATTERN.sub("<HEB>", text)


def split_notes_components(notes: str) -> tuple[str, str | None, str | None]:
    normalized_notes = INVISIBLE_MARK_PATTERN.sub("", notes)
    if not normalized_notes.startswith(NOTES_PREFIX):
        raise ValueError(f"unexpected notes format: {notes!r}")

    body = normalized_notes.removeprefix(NOTES_PREFIX)
    haketer_text = None
    if HAKETER_SEPARATOR in body:
        uxlc_text, haketer_text = body.split(HAKETER_SEPARATOR, 1)
    else:
        uxlc_text = body

    yatir = None
    uxlc_match = UXLC_YATIR_PATTERN.fullmatch(uxlc_text)
    if uxlc_match is not None:
        uxlc_text = uxlc_match.group("uxlc")
        yatir = uxlc_match.group("yatir")

    uxlc_text = uxlc_text.strip()
    if not uxlc_text:
        raise ValueError(f"unexpected empty UXLC notes component: {notes!r}")

    if haketer_text is not None:
        haketer_text = haketer_text.strip()
        if not haketer_text:
            raise ValueError(f"unexpected empty HaKeter notes component: {notes!r}")

    return (uxlc_text, yatir.strip() if yatir is not None else None, haketer_text)


def notes_structured_signature(notes: str) -> tuple[str, str | None, str | None]:
    notes_uxlc, notes_uxlc_yatir, notes_haketer = split_notes_components(notes)
    return (
        abstract_hebrew_runs(notes_uxlc),
        notes_uxlc_yatir,
        abstract_hebrew_runs(notes_haketer) if notes_haketer is not None else None,
    )


def apply_notes_fixes(row_data: dict[str, object]) -> None:
    current_notes = row_data.get("notes")
    if not isinstance(current_notes, str):
        return

    fixed_notes = strip_known_notes_junk(current_notes)
    targeted_fix_applied = False

    row_number = cast(int, row_data["row_number"])
    fix = NOTES_TARGETED_FIXES_BY_ROW_NUMBER.get(row_number)
    if fix is not None and fixed_notes == fix["original"]:
        fixed_notes = fix["fixed"]
        targeted_fix_applied = True

    if fixed_notes == current_notes:
        return

    if targeted_fix_applied:
        row_data["notes_orig"] = current_notes
    row_data["notes"] = fixed_notes


def assert_text_columns_before_drop(row_data: dict[str, object]) -> int:
    row_number = row_data["row_number"]

    entry_text = row_data.get("entry")
    if not isinstance(entry_text, str):
        raise ValueError(f"unexpected entry type at row {row_number}: {entry_text!r}")
    expected_entry = str(row_number)
    if entry_text != expected_entry:
        raise ValueError(
            f"unexpected entry text at row {row_number}: expected {expected_entry!r}, got {entry_text!r}"
        )

    aleppo_text = row_data.get("aleppo")
    if not isinstance(aleppo_text, str):
        raise ValueError(f"unexpected aleppo type at row {row_number}: {aleppo_text!r}")
    if aleppo_text != "":
        raise ValueError(f"unexpected non-empty aleppo text at row {row_number}: {aleppo_text!r}")

    leningrad_text = row_data.get("leningrad")
    if not isinstance(leningrad_text, str):
        raise ValueError(f"unexpected leningrad type at row {row_number}: {leningrad_text!r}")
    if leningrad_text not in ALLOWED_LENINGRAD_TEXT_VALUES:
        raise ValueError(f"unexpected leningrad text at row {row_number}: {leningrad_text!r}")
    return 1 if leningrad_text == "’" else 0


def source_document_reference(docx_path: Path) -> str:
    """Return a stable, repo-relative path when the source file is inside this repo."""
    try:
        relative = docx_path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return str(docx_path)
    return relative.as_posix()


def extract(docx_path: Path, output_dir: Path) -> dict[str, object]:
    image_dir = output_dir / "img"
    image_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx_path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
        relationships = ET.fromstring(archive.read("word/_rels/document.xml.rels"))

        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in relationships
            if rel.tag.endswith("Relationship")
        }

        body = document.find("w:body", NS)
        if body is None:
            raise ValueError("document body not found")

        intro_paragraphs: list[str] = []
        table_element: ET.Element | None = None
        for child in body:
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "p" and table_element is None:
                text = paragraph_text(child)
                if text:
                    intro_paragraphs.append(text)
                continue
            if tag == "tbl":
                table_element = child
                break

        if table_element is None:
            raise ValueError("no table found in document")

        table_rows = []
        for row in table_element.findall("./w:tr", NS):
            row_cells = []
            for cell in row.findall("./w:tc", NS):
                row_cells.append(cell_payload(cell, rel_map))
            table_rows.append(row_cells)

        header_row = table_rows[0]
        headers = [cell["text"] for cell in header_row]
        column_keys = [slugify(header if isinstance(header, str) else "") for header in headers]

        data_rows = []
        notes_signatures: list[tuple[str, str | None, str | None]] = []
        leningrad_quote_count = 0
        for row_index, row in enumerate(table_rows[1:], start=1):
            row_data: dict[str, object] = {
                "row_number": row_index,
            }
            image_refs: dict[str, list[str]] = {}
            for column_index, key in enumerate(column_keys):
                if column_index >= len(row):
                    row_data[key] = ""
                    continue

                payload = row[column_index]
                text = payload["text"]
                row_data[key] = text

                targets = payload["image_targets"]
                if targets:
                    image_refs[key] = export_images(
                        archive=archive,
                        row_number=row_index,
                        column_key=key,
                        targets=targets,
                        image_dir=image_dir,
                    )

            if image_refs:
                row_data["image_files"] = image_refs

            leningrad_quote_count += assert_text_columns_before_drop(row_data)
            apply_notes_fixes(row_data)

            notes = str(row_data["notes"])
            notes_uxlc, notes_uxlc_yatir, notes_haketer = split_notes_components(notes)

            # Preserve column order and place notes-* exactly where notes used to be.
            ordered_row_data: dict[str, object] = {
                "row_number": row_data["row_number"],
            }
            for key in column_keys:
                if key in {"entry", "aleppo", "leningrad"}:
                    continue
                if key == "notes":
                    ordered_row_data["notes-UXLC"] = notes_uxlc
                    ordered_row_data["notes-UXLC-yatir"] = notes_uxlc_yatir
                    ordered_row_data["notes-HaKeter"] = notes_haketer
                    continue
                ordered_row_data[key] = row_data[key]

            if "image_files" in row_data:
                ordered_row_data["image_files"] = row_data["image_files"]
            if "notes_orig" in row_data:
                ordered_row_data["notes_orig"] = row_data["notes_orig"]

            notes_signatures.append(notes_structured_signature(notes))
            data_rows.append(ordered_row_data)

        if leningrad_quote_count > 1:
            raise ValueError(
                "unexpected multiple non-empty leningrad text values; expected at most one "
                f"meaningless quote marker, found {leningrad_quote_count}"
            )

        verse_book_abbreviations = sorted(
            {verse_book_abbreviation(str(row["verse"])) for row in data_rows}
        )
        verse_book_name_by_abbreviation = {
            abbreviation: standard_book_name(abbreviation)
            for abbreviation in verse_book_abbreviations
        }
        finding_value_counts = [
            {
                "finding": finding,
                "count": count,
            }
            for finding, count in sorted(
                Counter(str(row["finding"]) for row in data_rows).items()
            )
        ]
        notes_structured_counts = [
            {
                "notes-UXLC": notes_uxlc,
                "notes-UXLC-yatir": notes_uxlc_yatir,
                "notes-HaKeter": notes_haketer,
                "count": count,
            }
            for (notes_uxlc, notes_uxlc_yatir, notes_haketer), count in sorted(
                Counter(notes_signatures).items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]

    intro_path = output_dir / "introduction.md"
    intro_path.write_text(intro_markdown(intro_paragraphs), encoding="utf-8")

    json_payload = {
        "source_document": source_document_reference(docx_path),
        "introduction_paragraph_count": len(intro_paragraphs),
        "table": {
            "header_labels": headers,
            "column_keys": column_keys,
            "row_count": len(data_rows),
            "finding_value_counts": finding_value_counts,
            "notes_structured_counts": notes_structured_counts,
            "verse_book_name_by_abbreviation": verse_book_name_by_abbreviation,
            "rows": data_rows,
        },
    }
    json_path = output_dir / "table_data.json"
    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    image_count = sum(
        len(paths)
        for row in data_rows
        for paths in row.get("image_files", {}).values()
    )
    return {
        "introduction_path": intro_path.as_posix(),
        "json_path": json_path.as_posix(),
        "image_dir": image_dir.as_posix(),
        "row_count": len(data_rows),
        "image_count": image_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract the introduction, table data, and embedded images from the source DOCX."
    )
    parser.add_argument(
        "docx_path",
        type=Path,
        nargs="?",
        default=DEFAULT_DOCX_PATH,
        help="Source DOCX to extract. Defaults to the tracked repo copy at repo top level.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs"),
        help="Directory where introduction.md, table_data.json, and img/ will be written.",
    )
    parser.add_argument(
        "--mam-parsed-path",
        type=Path,
        default=DEFAULT_MAM_PARSED_PATH,
        help="Path to sibling MAM-parsed repo used for mandatory post-extraction verification.",
    )
    args = parser.parse_args()

    summary = extract(docx_path=args.docx_path, output_dir=args.output_dir)
    table_json_path = args.output_dir / "table_data.json"
    verify_report = verify_table_words_in_mam_plus(
        table_json_path=table_json_path,
        mam_parsed_path=args.mam_parsed_path,
    )

    verify_summary = verify_report["summary"]
    if not isinstance(verify_summary, dict):
        raise ValueError("verification summary is invalid")

    missing_any = verify_summary["missing_any_plus_count"]
    missing_expected = verify_summary["missing_expected_plus_count"]
    summary["mam_plus_verify"] = verify_summary

    # Persist verification output inside extracted table_data.json.
    table_data = json.loads(table_json_path.read_text(encoding="utf-8"))
    if not isinstance(table_data, dict):
        raise ValueError("extracted table_data.json root must be an object")
    table_data["mam_plus_verify"] = verify_summary
    table_json_path.write_text(
        json.dumps(table_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if missing_any or missing_expected:
        raise ValueError(
            "post-extraction verification failed: "
            f"missing_any_plus_count={missing_any}, "
            f"missing_expected_plus_count={missing_expected}"
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()