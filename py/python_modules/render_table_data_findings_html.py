from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from html import escape
import os
from pathlib import Path
from typing import Any

from python_modules.json_io import load_json
from python_modules.holam_he_validation import (
    evaluate_holam_he_row,
    require_holam_he_row_match,
)
from python_modules.mam_uxlc_diff_descriptions import simple_row_diff_note_lines
from python_modules.mpp_matching_template_args import (
    matching_template_arguments_in_mpp_verse_by_row_number,
)
from python_modules.qyv_validation import evaluate_qyv_row, require_qyv_row_match
from python_modules.table_data_external_links import verse_external_links
from python_modules.table_row_github_issues import (
    ISSUE_TAG_DISPLAY_TEXT,
    require_row_github_issue_metadata,
    row_github_issue_url,
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
MPP_TEMPLATE_FILTER_ID = "has-mpp-template"
MPP_TEMPLATE_FILTER_LABEL = "Has matching MPP template"
NO_ISSUE_TAG = "no-issue-tag"
NO_ISSUE_TAG_LABEL = "no issue tag"
FINDING_INVARIANT_SUFFIX = " | L - Qere"
FINDING_DISPLAY_MAP = {
    "A and L - Qere": "A - Qere note",
}
ISSUE_TAG_ORDER = (
    "holam-he",
    "qyv",
    "boa-sans-aleph",
    "rafeh",
    NO_ISSUE_TAG,
)
SUMMARY_ISSUE_TAG_FILTER_IDS = frozenset(
    {
        "issue-tag-holam-he",
        "issue-tag-qyv",
        "issue-tag-boa-sans-aleph",
        "issue-tag-rafeh",
        "issue-tag-no-issue-tag",
    }
)
MAIN_NAV_LABEL = "Active"
SUPPRESSED_NAV_LABEL = "Suppressed"
MAIN_PAGE_TITLE = "Holman k/q"
SUPPRESSED_PAGE_TITLE = "Holman k/q - Suppressed"
MAIN_PAGE_HEADING = "Holman ketiv/qere review"
SUPPRESSED_PAGE_HEADING = "Suppressed"

# Per-image display-size tweaks measured against each image's native width.
# Key format: (row_number, witness, image_index_1_based)
IMAGE_NATIVE_SCALE_TWEAKS: dict[tuple[str, str, int], float] = {
    ("4", "aleppo", 1): 0.5,
    ("5", "aleppo", 1): 0.5,
    ("6", "aleppo", 1): 0.5,
    ("7", "aleppo", 1): 0.5,
    ("74", "aleppo", 1): 0.5,
}
HEBREW_CHAR_RANGES = (("\u0590", "\u05ff"), ("\ufb1d", "\ufb4f"))
HOLAM_HE_TAG = "holam-he"
QYV_TAG = "qyv"


@dataclass(frozen=True)
class FilterCategory:
    filter_id: str
    label: str
    count: int


def render_table_data_findings_html(
    table_json_path: Path, output_html_path: Path
) -> Path:
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

    _validate_issue_tag_definitions(rows)

    matching_template_arguments_by_row_number = (
        matching_template_arguments_in_mpp_verse_by_row_number(payload)
    )
    source_document = _as_text(payload.get("source_document", ""))
    finding_counts = Counter(_as_text(row.get("finding", "")) for row in rows)
    sorted_findings = sorted(
        finding_counts.items(), key=lambda item: (-item[1], item[0])
    )
    finding_ids = {
        finding: f"f{idx:02d}" for idx, (finding, _count) in enumerate(sorted_findings)
    }

    css_output_path = output_html_path.with_suffix(".css")
    js_output_path = output_html_path.with_suffix(".js")
    _write_report_assets(
        css_output_path=css_output_path,
        js_output_path=js_output_path,
        finding_ids=list(finding_ids.values()),
    )

    active_rows, suppressed_rows = _partition_rows(rows)
    suppressed_output_path = _suppressed_output_path(output_html_path)

    _write_report_page(
        page_title=MAIN_PAGE_TITLE,
        page_heading=MAIN_PAGE_HEADING,
        page_subtitle="",
        rows=active_rows,
        sorted_findings=sorted_findings,
        finding_ids=finding_ids,
        matching_template_arguments_by_row_number=matching_template_arguments_by_row_number,
        output_html_path=output_html_path,
        css_output_path=css_output_path,
        js_output_path=js_output_path,
        repo_root=table_json_path.parent.parent,
        main_output_path=output_html_path,
        suppressed_output_path=suppressed_output_path,
        active_nav_label=MAIN_NAV_LABEL,
        records_heading="Records",
    )
    _write_report_page(
        page_title=SUPPRESSED_PAGE_TITLE,
        page_heading=SUPPRESSED_PAGE_HEADING,
        page_subtitle="Closed issues only",
        rows=suppressed_rows,
        sorted_findings=sorted_findings,
        finding_ids=finding_ids,
        matching_template_arguments_by_row_number=matching_template_arguments_by_row_number,
        output_html_path=suppressed_output_path,
        css_output_path=css_output_path,
        js_output_path=js_output_path,
        repo_root=table_json_path.parent.parent,
        main_output_path=output_html_path,
        suppressed_output_path=suppressed_output_path,
        active_nav_label=SUPPRESSED_NAV_LABEL,
        records_heading="Suppressed Records",
    )
    return output_html_path


def _write_report_page(
    *,
    page_title: str,
    page_heading: str,
    page_subtitle: str,
    rows: list[dict[str, Any]],
    sorted_findings: list[tuple[str, int]],
    finding_ids: dict[str, str],
    matching_template_arguments_by_row_number: dict[str, list[dict[str, str]]],
    output_html_path: Path,
    css_output_path: Path,
    js_output_path: Path,
    repo_root: Path,
    main_output_path: Path,
    suppressed_output_path: Path,
    active_nav_label: str,
    records_heading: str,
) -> None:
    categories = _filter_categories(
        rows=rows,
        sorted_findings=sorted_findings,
        finding_ids=finding_ids,
        matching_template_arguments_by_row_number=matching_template_arguments_by_row_number,
    )
    summary_rows = _summary_rows_html(categories)
    cards = "\n".join(
        _record_card_html(
            row=row,
            finding_id=finding_ids[_as_text(row.get("finding", ""))],
            output_html_path=output_html_path,
            repo_root=repo_root,
            matching_template_arguments_by_row_number=matching_template_arguments_by_row_number,
        )
        for row in rows
    )

    css_href = escape(
        os.path.relpath(css_output_path, output_html_path.parent).replace("\\", "/")
    )
    js_src = escape(
        os.path.relpath(js_output_path, output_html_path.parent).replace("\\", "/")
    )
    nav_html = _top_nav_html(
        current_output_path=output_html_path,
        main_output_path=main_output_path,
        suppressed_output_path=suppressed_output_path,
        active_nav_label=active_nav_label,
    )
    page_total = len(rows)
    summary_html = f'<div class="summary-columns">{summary_rows}</div>'
    page_subtitle_html = (
        "" if not page_subtitle else f'<p class="subtitle">{escape(page_subtitle)}</p>'
    )

    html = f"""<!DOCTYPE html>
<html lang=\"he\" dir=\"ltr\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{escape(page_title)}</title>
<link rel=\"stylesheet\" href=\"{css_href}\">
</head>
<body>
{nav_html}
<h1>{escape(page_heading)}</h1>
{page_subtitle_html}
<div class=\"meta-grid\">
    <div class=\"meta-box\"><div class=\"meta-label\">Total Records</div><div class=\"meta-value\">{page_total}</div></div>
    <div class=\"meta-box\"><div class=\"meta-label\">Visible/Filtered-out records</div><div class=\"meta-value\" id=\"visible-filtered-count\">{page_total}/0</div></div>
</div>
{summary_html}
<h2 class=\"section-title\">{escape(records_heading)}</h2>
<div class=\"records\">{cards}</div>
<script src=\"{js_src}\" defer></script>
</body>
</html>
"""

    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(html, encoding="utf-8")


def _validate_issue_tag_definitions(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row_number = _as_text(row.get("row_number", ""))
        metadata = require_row_github_issue_metadata(row_number)

        holam_he_evaluation = evaluate_holam_he_row(row)
        if HOLAM_HE_TAG in metadata.tags:
            require_holam_he_row_match(
                row,
                context="tagged holam-he in findings renderer",
            )
        elif holam_he_evaluation.matches:
            raise ValueError(
                f"row {holam_he_evaluation.row_number} {holam_he_evaluation.verse} matches the holam-he definition but is missing the holam-he tag (findings renderer coverage check)"
            )

        evaluation = evaluate_qyv_row(row)
        if QYV_TAG in metadata.tags:
            require_qyv_row_match(row, context="tagged QyV in findings renderer")
            continue
        if evaluation.matches:
            raise ValueError(
                f"row {evaluation.row_number} {evaluation.verse} matches the QyV definition but is missing the qyv tag (findings renderer coverage check)"
            )


def _partition_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active_rows: list[dict[str, Any]] = []
    suppressed_rows: list[dict[str, Any]] = []
    for row in rows:
        row_number = _as_text(row.get("row_number", ""))
        metadata = require_row_github_issue_metadata(row_number)
        if metadata.is_closed:
            suppressed_rows.append(row)
        else:
            active_rows.append(row)
    return active_rows, suppressed_rows


def _filter_categories(
    *,
    rows: list[dict[str, Any]],
    sorted_findings: list[tuple[str, int]],
    finding_ids: dict[str, str],
    matching_template_arguments_by_row_number: dict[str, list[dict[str, str]]],
) -> list[FilterCategory]:
    categories: list[FilterCategory] = []
    finding_counts = Counter(_as_text(row.get("finding", "")) for row in rows)
    for finding, _count in sorted_findings:
        count = finding_counts.get(finding, 0)
        if count == 0:
            continue
        categories.append(
            FilterCategory(
                filter_id=finding_ids[finding],
                label=_finding_display_text(finding),
                count=count,
            )
        )

    mpp_template_filter_count = sum(
        1
        for row in rows
        if matching_template_arguments_by_row_number.get(
            _as_text(row.get("row_number", "")), []
        )
    )
    if mpp_template_filter_count:
        categories.append(
            FilterCategory(
                filter_id=MPP_TEMPLATE_FILTER_ID,
                label=MPP_TEMPLATE_FILTER_LABEL,
                count=mpp_template_filter_count,
            )
        )

    for issue_tag in ISSUE_TAG_ORDER:
        count = sum(
            1
            for row in rows
            if issue_tag
            in _record_issue_tags(
                require_row_github_issue_metadata(
                    _as_text(row.get("row_number", ""))
                ).tags
            )
        )
        if count == 0:
            continue
        categories.append(
            FilterCategory(
                filter_id=_issue_tag_filter_id(issue_tag),
                label=_issue_tag_display_text(issue_tag),
                count=count,
            )
        )
    return categories


def _suppressed_output_path(output_html_path: Path) -> Path:
    return output_html_path.with_name(
        f"{output_html_path.stem}_suppressed{output_html_path.suffix}"
    )


def _top_nav_html(
    *,
    current_output_path: Path,
    main_output_path: Path,
    suppressed_output_path: Path,
    active_nav_label: str,
) -> str:
    main_href = escape(
        os.path.relpath(main_output_path, current_output_path.parent).replace("\\", "/")
    )
    suppressed_href = escape(
        os.path.relpath(suppressed_output_path, current_output_path.parent).replace(
            "\\", "/"
        )
    )
    main_class = "nav-link active" if active_nav_label == MAIN_NAV_LABEL else "nav-link"
    suppressed_class = (
        "nav-link active" if active_nav_label == SUPPRESSED_NAV_LABEL else "nav-link"
    )
    return (
        '<nav class="top-nav">'
        f'<a class="{main_class}" href="{main_href}">{MAIN_NAV_LABEL}</a>'
        f'<a class="{suppressed_class}" href="{suppressed_href}">{SUPPRESSED_NAV_LABEL}</a>'
        "</nav>"
    )


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


def _summary_row_html(category: FilterCategory) -> str:
    return (
        f'<tr data-filter-id="{escape(category.filter_id)}">'
        f'<td><span class="cat-swatch cat-{escape(category.filter_id)}"></span>{escape(category.label)}</td>'
        f"<td>{category.count}</td></tr>"
    )


def _summary_rows_html(categories: list[FilterCategory]) -> str:
    grouped_sections: list[str] = []
    finding_categories = [
        category
        for category in categories
        if not category.filter_id.startswith("issue-tag-")
        and category.filter_id != MPP_TEMPLATE_FILTER_ID
    ]
    grouped_categories = (
        (
            "Aleppo notation",
            finding_categories,
        ),
        (
            "Issue tags",
            [
                category
                for category in categories
                if category.filter_id in SUMMARY_ISSUE_TAG_FILTER_IDS
            ],
        ),
        (
            "MPP",
            [
                category
                for category in categories
                if category.filter_id == MPP_TEMPLATE_FILTER_ID
            ],
        ),
    )
    for group_title, group_categories in grouped_categories:
        if not group_categories:
            continue
        group_rows = "\n".join(
            _summary_row_html(category) for category in group_categories
        )
        grouped_sections.append(_summary_group_html(group_title, group_rows))
    return "\n".join(grouped_sections)


def _summary_group_html(group_title: str, rows_html: str) -> str:
    return (
        f'<section class="summary-group"><h2 class="summary-group-title">{escape(group_title)}</h2>'
        f'<table class="summary">{rows_html}</table></section>'
    )


def _record_card_html(
    row: dict[str, Any],
    finding_id: str,
    output_html_path: Path,
    repo_root: Path,
    matching_template_arguments_by_row_number: dict[str, list[dict[str, str]]],
) -> str:
    row_number = _as_text(row.get("row_number", ""))
    metadata = require_row_github_issue_metadata(row_number)
    row_fragment_id = _row_fragment_id(row_number)
    verse = _as_text(row.get("verse", ""))
    verse_ref_html = _verse_ref_html(verse=verse, row_number=row_number)
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
    record_categories: list[tuple[str, str]] = [(finding_id, finding_display)]
    if matching_template_args_in_mpp_verse:
        record_categories.append((MPP_TEMPLATE_FILTER_ID, MPP_TEMPLATE_FILTER_LABEL))
    record_categories.extend(
        (
            _issue_tag_filter_id(issue_tag),
            _issue_tag_display_text(issue_tag),
        )
        for issue_tag in _record_issue_tags(metadata.tags)
    )
    filter_ids_attr = " ".join(filter_id for filter_id, _label in record_categories)
    category_badges_html = "".join(
        _record_category_badge_html(filter_id=filter_id, label=label)
        for filter_id, label in record_categories
    )
    simple_diff_notes_html = "".join(
        _note_line_html(label=label, value=value)
        for label, value in simple_row_diff_note_lines(
            row,
            issue_tags=metadata.tags,
        )
    )

    yatir_html = (
        ""
        if notes_uxlc_yatir is None
        else _note_line_html(
            label="UXLC yatir:",
            value=notes_uxlc_yatir,
            strip_prefix="yatir ",
        )
    )
    haketer_html = (
        ""
        if notes_haketer is None
        else (
            f'<div class="note-line"><span class="label">HaKeter:</span><bdi class="pointed-heb">{escape(notes_haketer)}</bdi></div>'
        )
    )
    differing_latest_mpp_words: list[str] = []
    for match in matching_template_args_in_mpp_verse:
        argument_text = _as_text(match.get("argument_text"))
        if argument_text == word or argument_text in differing_latest_mpp_words:
            continue
        differing_latest_mpp_words.append(argument_text)
    rendered_mam_words = {word, *differing_latest_mpp_words}
    displayed_matching_template_args_in_mpp_verse = [
        match
        for match in matching_template_args_in_mpp_verse
        if _as_text(match.get("argument_text")) not in rendered_mam_words
    ]
    mpp_matching_template_arg_html = "".join(
        (
            f'<div class="note-line"><span class="label">'
            f'MPP matching template arg ({escape(_as_text(match.get("template_name")))}'
            f'[{escape(_as_text(match.get("argument_key")))}]):'
            f'</span><bdi class="pointed-heb">'
            f'{escape(_as_text(match.get("argument_text")))}</bdi></div>'
        )
        for match in displayed_matching_template_args_in_mpp_verse
    )
    mam_word_label = (
        "MAM Word (from docx):" if differing_latest_mpp_words else "MAM Word:"
    )
    mam_word_html = (
        f'<div class="note-line"><span class="label">{mam_word_label}</span>'
        f'<bdi class="pointed-heb">{escape(word)}</bdi></div>'
    )
    if differing_latest_mpp_words:
        mam_word_html += (
            f'\n<div class="note-line"><span class="label">MAM Word (from latest MPP):</span>'
            f'<bdi class="pointed-heb">{escape(" | ".join(differing_latest_mpp_words))}</bdi></div>'
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

    return f"""<article id="{row_fragment_id}" class="record-card" data-finding-id="{finding_id}" data-filter-ids="{escape(filter_ids_attr)}">
<div class="record-head"><span class="record-ref">#{escape(row_number)}</span><span class="record-verse">{verse_ref_html}</span><span class="category-badges">{category_badges_html}</span></div>
<div class="record-grid"><div>
{mam_word_html}
<div class="note-line"><span class="label">UXLC:</span><bdi class="pointed-heb">{escape(notes_uxlc)}</bdi></div>
{simple_diff_notes_html}{yatir_html}{haketer_html}{mpp_matching_template_arg_html}
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
        return f'<span class="label">No {escape(label)} image</span>'

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
            f'<a href="{rel_asset_html}" target="_blank" rel="noopener">'
            f'<img class="image-thumb" src="{rel_asset_html}" alt="{escape(label)} image {index}"{native_scale_attr}></a>'
        )

    if not rendered:
        return f'<span class="label">No {escape(label)} image</span>'
    return "".join(rendered)


def _verse_ref_html(verse: str, row_number: str) -> str:
    links = verse_external_links(verse)
    issue_url = row_github_issue_url(row_number)
    issue_html = ""
    if issue_url is not None:
        issue_html = (
            f' <a href="{escape(issue_url)}" target="_blank" rel="noopener">issue</a>'
        )
    return (
        f"{escape(verse)} "
        f'<a href="{escape(links.mgketer_url)}" target="_blank" rel="noopener">mgketer</a>'
        f' <a href="{escape(links.mwd_url)}" target="_blank" rel="noopener">MwD</a>'
        f' <a href="{escape(links.mam_ws_url)}" target="_blank" rel="noopener">MAM-ws</a>'
        f"{issue_html}"
    )


def _note_line_html(label: str, value: str, strip_prefix: str | None = None) -> str:
    display_value = value.strip()
    if strip_prefix is not None and display_value.startswith(strip_prefix):
        display_value = display_value[len(strip_prefix) :].lstrip()

    if _contains_hebrew_char(display_value):
        value_html = f'<bdi class="pointed-heb">{escape(display_value)}</bdi>'
    else:
        value_html = f"<span>{escape(display_value)}</span>"

    return f'<div class="note-line"><span class="label">{escape(label)}</span> {value_html}</div>'


def _contains_hebrew_char(text: str) -> bool:
    return any(
        start <= char <= end for char in text for start, end in HEBREW_CHAR_RANGES
    )


def _row_fragment_id(row_number: str) -> str:
    return f"row{int(row_number):02d}"


def _issue_tag_filter_id(issue_tag: str) -> str:
    return f"issue-tag-{issue_tag}"


def _issue_tag_display_text(issue_tag: str) -> str:
    return ISSUE_TAG_DISPLAY_TEXT.get(issue_tag, issue_tag)


def _record_issue_tags(issue_tags: list[str]) -> list[str]:
    ordered_issue_tags = _ordered_issue_tags(issue_tags)
    return ordered_issue_tags if ordered_issue_tags else [NO_ISSUE_TAG]


def _ordered_issue_tags(issue_tags: list[str]) -> list[str]:
    known_tags = [issue_tag for issue_tag in ISSUE_TAG_ORDER if issue_tag in issue_tags]
    extra_tags = sorted(
        issue_tag for issue_tag in issue_tags if issue_tag not in ISSUE_TAG_ORDER
    )
    return known_tags + extra_tags


def _record_category_badge_html(*, filter_id: str, label: str) -> str:
    return (
        f'<span class="finding-badge cat-{escape(filter_id)}">'
        f"{escape(label)}</span>"
    )


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
