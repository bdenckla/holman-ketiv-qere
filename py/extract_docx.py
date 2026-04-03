from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

CONTROL_CHARS = {
    "\u00a0": " ",
}

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCX_PATH = REPO_ROOT / "source" / "Review of Qere and Kethib readings in the Aleppo and Leningrad.docx"


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
            data_rows.append(row_data)

    intro_path = output_dir / "introduction.md"
    intro_path.write_text(intro_markdown(intro_paragraphs), encoding="utf-8")

    json_payload = {
        "source_document": str(docx_path),
        "introduction_paragraph_count": len(intro_paragraphs),
        "table": {
            "header_labels": headers,
            "column_keys": column_keys,
            "row_count": len(data_rows),
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
        help="Source DOCX to extract. Defaults to the tracked repo copy under source/.",
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