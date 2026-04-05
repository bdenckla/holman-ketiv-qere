from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from python_modules.json_io import load_json, write_json
from python_modules.extract_docx_pipeline import parse_docx_archive, write_extract_files
from python_modules.verify_table_words_in_mam_plus import verify_table_words_in_mam_plus

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCX_PATH = REPO_ROOT / "Review of Qere and Kethib readings in the Aleppo and Leningrad.docx"
DEFAULT_MAM_PARSED_PATH = REPO_ROOT.parent / "MAM-parsed"


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
        parsed = parse_docx_archive(archive=archive, image_dir=image_dir)

    intro_path, json_path = write_extract_files(
        output_dir=output_dir,
        source_document=source_document_reference(docx_path),
        parsed=parsed,
    )

    image_count = sum(
        len(paths)
        for row in parsed.data_rows
        for paths in row.get("image_files", {}).values()
    )
    return {
        "introduction_path": intro_path.as_posix(),
        "json_path": json_path.as_posix(),
        "image_dir": image_dir.as_posix(),
        "row_count": len(parsed.data_rows),
        "image_count": image_count,
    }


def persist_verify_summary(table_json_path: Path, verify_report: dict[str, object]) -> None:
    """Persist verification output inside extracted table_data.json."""
    table_data = load_json(table_json_path)
    if not isinstance(table_data, dict):
        raise ValueError("extracted table_data.json root must be an object")

    verify_summary = verify_report.get("summary")
    if not isinstance(verify_summary, dict):
        raise ValueError("verification summary is invalid")

    doc_note_rows = verify_report.get("rows_matching_expected_nusach_target")
    if not isinstance(doc_note_rows, list):
        raise ValueError("verification rows_matching_expected_nusach_target is invalid")

    table_data["mam_plus_verify"] = verify_summary
    table_data["mam_plus_rows_matching_expected_nusach_target"] = doc_note_rows
    write_json(table_json_path, table_data)


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
    persist_verify_summary(table_json_path=table_json_path, verify_report=verify_report)

    if missing_any or missing_expected:
        raise ValueError(
            "post-extraction verification failed: "
            f"missing_any_plus_count={missing_any}, "
            f"missing_expected_plus_count={missing_expected}"
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()