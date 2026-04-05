from __future__ import annotations

from collections import Counter
from html import escape
import os
from pathlib import Path
from typing import Any

from python_modules.json_io import load_json
from python_modules.mpp_matching_template_args import (
    matching_template_arguments_in_mpp_verse_by_row_number,
)

PALETTE = [
    "#1f5f8b",
    "#2e8b57",
    "#a2472f",
    "#6a4c93",
    "#7a5f00",
    "#3e6b7f",
    "#8b3a62",
    "#4f6d2e",
    "#505c91",
    "#9c4a22",
]

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CSS_TEMPLATE_PATH = ASSETS_DIR / "table_data_findings.css"
JS_TEMPLATE_PATH = ASSETS_DIR / "table_data_findings.js"
CSS_COLOR_PLACEHOLDER = "/* __FINDING_COLORS__ */"
FINDING_INVARIANT_SUFFIX = " | L - Qere"
FINDING_DISPLAY_MAP = {
    "A and L - Qere": "A - Qere note",
}
# Per-image display-size tweaks measured against each image's native width.
# Key format: (row_number, witness, image_index_1_based)
IMAGE_NATIVE_SCALE_TWEAKS: dict[tuple[str, str, int], float] = {
    ("4", "aleppo", 1): 0.5,
    ("5", "aleppo", 1): 0.5,
    ("6", "aleppo", 1): 0.5,
    ("7", "aleppo", 1): 0.5,
    ("74", "aleppo", 1): 0.5,
}


def render_table_data_findings_html(table_json_path: Path, output_html_path: Path) -> Path:
    payload = load_json(table_json_path)
    if not isinstance(payload, dict):
        raise ValueError("table_data.json root must be an object")
    table = payload.get("table")
    if not isinstance(table, dict):
        raise ValueError("table_data.json missing table object")
    rows_obj = table.get("rows")
    if not isinstance(rows_obj, list):
        raise ValueError("table_data.json table.rows must be a list")

    rows = [row for row in rows_obj if isinstance(row, dict)]
    if len(rows) != len(rows_obj):
        raise ValueError("table_data.json table.rows must contain only objects")

    matching_template_arguments_by_row_number = matching_template_arguments_in_mpp_verse_by_row_number(
        payload
    )

    total_count = len(rows)
    source_document = _as_text(payload.get("source_document", ""))
    finding_counts = Counter(_as_text(row.get("finding", "")) for row in rows)
    sorted_findings = sorted(finding_counts.items(), key=lambda item: (-item[1], item[0]))
    finding_ids = {finding: f"f{idx:02d}" for idx, (finding, _count) in enumerate(sorted_findings)}

    css_output_path = output_html_path.with_suffix(".css")
    js_output_path = output_html_path.with_suffix(".js")
    _write_report_assets(
        css_output_path=css_output_path,
        js_output_path=js_output_path,
        finding_ids=list(finding_ids.values()),
    )

    summary_rows = "\n".join(
        _summary_row_html(finding=finding, count=count, finding_id=finding_ids[finding])
        for finding, count in sorted_findings
    )
    filter_buttons = "\n".join(
        _filter_button_html(finding=finding, count=count, finding_id=finding_ids[finding])
        for finding, count in sorted_findings
    )
    cards = "\n".join(
        _record_card_html(
            row=row,
            finding_id=finding_ids[_as_text(row.get("finding", ""))],
            output_html_path=output_html_path,
            repo_root=table_json_path.parent.parent,
            matching_template_arguments_by_row_number=matching_template_arguments_by_row_number,
        )
        for row in rows
    )

    css_href = escape(css_output_path.name)
    js_src = escape(js_output_path.name)

    html = f"""<!DOCTYPE html>
<html lang=\"he\" dir=\"ltr\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>Table Findings</title>
<link rel=\"stylesheet\" href=\"{css_href}\">
</head>
<body>
<h1>Finding-Based Table Report</h1>
<p class=\"subtitle\">Source: {escape(source_document)}</p>
<div class=\"meta-grid\">
  <div class=\"meta-box\"><div class=\"meta-label\">Total Records</div><div class=\"meta-value\">{total_count}</div></div>
  <div class=\"meta-box\"><div class=\"meta-label\">Visible Records</div><div class=\"meta-value\" id=\"visible-count\">{total_count}</div></div>
  <div class=\"meta-box\"><div class=\"meta-label\">Unique Finding Values</div><div class=\"meta-value\">{len(sorted_findings)}</div></div>
</div>
<h2 class=\"section-title\">Summary by finding</h2>
<table class=\"summary\"><tr><th>Finding</th><th>Count</th></tr>
{summary_rows}
<tr class=\"total-row\"><td>Total</td><td>{total_count}</td></tr></table>
<h2 class=\"section-title\">Filter</h2>
<div class=\"filter-bar\"><button type=\"button\" class=\"filter-btn\" id=\"show-all-btn\">Show all</button>
{filter_buttons}
</div>
<h2 class=\"section-title\">Records</h2>
<div class=\"records\">{cards}</div>
<script src=\"{js_src}\" defer></script>
</body>
</html>
"""

    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(html, encoding="utf-8")
    return output_html_path


def _write_report_assets(
    css_output_path: Path,
    js_output_path: Path,
    finding_ids: list[str],
) -> None:
    color_rules = "\n".join(
        f".cat-{finding_id} {{ background: {PALETTE[idx % len(PALETTE)]}; }}"
        for idx, finding_id in enumerate(finding_ids)
    )

    css_template = CSS_TEMPLATE_PATH.read_text(encoding="utf-8")
    css_text = css_template.replace(CSS_COLOR_PLACEHOLDER, color_rules)
    js_text = JS_TEMPLATE_PATH.read_text(encoding="utf-8")

    css_output_path.parent.mkdir(parents=True, exist_ok=True)
    js_output_path.parent.mkdir(parents=True, exist_ok=True)
    css_output_path.write_text(css_text, encoding="utf-8")
    js_output_path.write_text(js_text, encoding="utf-8")


def _summary_row_html(finding: str, count: int, finding_id: str) -> str:
    finding_display = _finding_display_text(finding)
    return (
        f"<tr data-finding-id=\"{finding_id}\">"
        f"<td><span class=\"cat-swatch cat-{finding_id}\"></span>{escape(finding_display)}</td>"
        f"<td>{count}</td></tr>"
    )


def _filter_button_html(finding: str, count: int, finding_id: str) -> str:
    finding_display = _finding_display_text(finding)
    return (
        f"<button type=\"button\" class=\"filter-btn\" data-finding-id=\"{finding_id}\">"
        f"{escape(finding_display)} ({count})</button>"
    )


def _record_card_html(
    row: dict[str, Any],
    finding_id: str,
    output_html_path: Path,
    repo_root: Path,
    matching_template_arguments_by_row_number: dict[str, list[dict[str, str]]],
) -> str:
    row_number = _as_text(row.get("row_number", ""))
    verse = _as_text(row.get("verse", ""))
    word = _as_text(row.get("word", ""))
    finding = _as_text(row.get("finding", ""))
    finding_display = _finding_display_text(finding)
    notes_uxlc = _as_text(row.get("notes-UXLC", ""))
    notes_uxlc_yatir = _as_optional_text(row.get("notes-UXLC-yatir"))
    notes_haketer = _as_optional_text(row.get("notes-HaKeter"))
    raw_images = row.get("image_files")
    images: dict[str, object] = raw_images if isinstance(raw_images, dict) else {}
    matching_template_args_in_mpp_verse = matching_template_arguments_by_row_number.get(
        row_number, []
    )

    yatir_html = "" if notes_uxlc_yatir is None else (
        f"<div class=\"note-line\"><span class=\"label\">UXLC yatir:</span><bdi class=\"pointed-heb\">{escape(notes_uxlc_yatir)}</bdi></div>"
    )
    haketer_html = "" if notes_haketer is None else (
        f"<div class=\"note-line\"><span class=\"label\">HaKeter:</span><bdi class=\"pointed-heb\">{escape(notes_haketer)}</bdi></div>"
    )
    mpp_matching_template_arg_html = "".join(
        (
            f"<div class=\"note-line\"><span class=\"label\">"
            f"MPP matching template arg ({escape(_as_text(match.get('template_name')))}"
            f"[{escape(_as_text(match.get('argument_key')))}]):"
            f"</span><bdi class=\"pointed-heb\">"
            f"{escape(_as_text(match.get('argument_text')))}</bdi></div>"
        )
        for match in matching_template_args_in_mpp_verse
    )
    aleppo = _image_paths_html(
        image_paths=images.get("aleppo"),
        witness="aleppo",
        label="Aleppo",
        row_number=row_number,
        output_html_path=output_html_path,
        repo_root=repo_root,
    )
    leningrad = _image_paths_html(
        image_paths=images.get("leningrad"),
        witness="leningrad",
        label="Leningrad",
        row_number=row_number,
        output_html_path=output_html_path,
        repo_root=repo_root,
    )

    return f"""<article class="record-card" data-finding-id="{finding_id}">
<div class="record-head"><span class="record-ref">#{escape(row_number)}</span><span class="record-verse">{escape(verse)}</span><span class="finding-badge cat-{finding_id}">{escape(finding_display)}</span></div>
<div class="record-grid"><div>
<div class="note-line"><span class="label">MAM Word:</span><bdi class="pointed-heb">{escape(word)}</bdi></div>
<div class="note-line"><span class="label">UXLC:</span><bdi class="pointed-heb">{escape(notes_uxlc)}</bdi></div>
{yatir_html}{haketer_html}{mpp_matching_template_arg_html}
</div><div>
<div class="image-panel"><div class="image-caption">Aleppo</div><div class="image-strip">{aleppo}</div></div>
<div class="image-panel" style="margin-top:.45rem;"><div class="image-caption">Leningrad</div><div class="image-strip">{leningrad}</div></div>
</div></div></article>"""


def _image_paths_html(
    image_paths: object,
    witness: str,
    label: str,
    row_number: str,
    output_html_path: Path,
    repo_root: Path,
) -> str:
    if not isinstance(image_paths, list):
        return f"<span class=\"label\">No {escape(label)} image</span>"

    output_dir = output_html_path.parent.resolve()
    rendered: list[str] = []
    for index, path_obj in enumerate(image_paths, start=1):
        if not isinstance(path_obj, str) or not path_obj.strip():
            continue
        absolute_asset = (repo_root / path_obj.replace("\\", "/")).resolve()
        rel_asset = os.path.relpath(absolute_asset, output_dir).replace("\\", "/")
        rel_asset_html = escape(rel_asset)
        native_scale = IMAGE_NATIVE_SCALE_TWEAKS.get((row_number, witness, index))
        native_scale_attr = ""
        if native_scale is not None:
            native_scale_attr = f' data-native-scale="{native_scale:g}"'
        rendered.append(
            f"<a href=\"{rel_asset_html}\" target=\"_blank\" rel=\"noopener\">"
            f"<img class=\"image-thumb\" src=\"{rel_asset_html}\" alt=\"{escape(label)} image {index}\"{native_scale_attr}></a>"
        )

    if not rendered:
        return f"<span class=\"label\">No {escape(label)} image</span>"
    return "".join(rendered)


def _as_text(value: object) -> str:
    return "" if value is None else str(value)


def _finding_display_text(finding: str) -> str:
    if finding.endswith(FINDING_INVARIANT_SUFFIX):
        finding = finding[: -len(FINDING_INVARIANT_SUFFIX)]
    return FINDING_DISPLAY_MAP.get(finding, finding)


def _as_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None
