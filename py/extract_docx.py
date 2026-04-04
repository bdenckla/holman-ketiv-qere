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

NOTES_JUNK_REPLACEMENTS = (
    ("y\u202c\u200f", ""),
    ("\u202c\u202c", ""),
)

NOTES_TARGETED_FIXES_BY_ROW_NUMBER = {
    37: {
        "original": "MAM - No Comments | UXLC - מַה־לִּי־פֹה֙ מי־לי־",
        "fixed": "MAM - No Comments | UXLC - לי־ מַה־לִּי־פֹה֙",
    },
}


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


def apply_notes_fixes(row_data: dict[str, object]) -> None:
    current_notes = row_data.get("notes")
    if not isinstance(current_notes, str):
        return

    fixed_notes = strip_known_notes_junk(current_notes)

    row_number = cast(int, row_data["row_number"])
    fix = NOTES_TARGETED_FIXES_BY_ROW_NUMBER.get(row_number)
    if fix is not None and fixed_notes == fix["original"]:
        fixed_notes = fix["fixed"]

    if fixed_notes == current_notes:
        return

    row_data["notes_orig"] = current_notes
    row_data["notes"] = fixed_notes


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

            apply_notes_fixes(row_data)
            data_rows.append(row_data)

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
    args = parser.parse_args()

    summary = extract(docx_path=args.docx_path, output_dir=args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()