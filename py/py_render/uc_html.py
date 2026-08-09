"""Build gh-pages/uxlc_corrections.html from the emails under emails/."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import json
from pathlib import Path
import struct

from py_render.rt_assets import PALETTE
from py_render.uc_case_card import (
    case_card_html,
    case_filter_ids,
    case_fragment_id,
    email_filter_id,
    email_fragment_id,
    relative_href,
)
from py_render.uc_hebrew_runs import inline_text_html
from py_render.uc_summary import all_filter_ids, summary_html
from python_modules.uxlc_case_tags import (
    SUGGESTION_KIND_LABELS,
    require_full_coverage,
    suggestion_kind,
)
from python_modules.uxlc_email_extract import (
    ADDRESS_REDACTION,
    CorrectionCase,
    SourceEmail,
    read_emails,
)
from python_modules.uxlc_external_links import book_display_name
from python_modules.uxlc_manuscript_page import manuscript_page
from uxlc_comments.all_comments import BY_REF as COMMENTS_BY_REF, comments_for_ref

PAGE_TITLE = "Holman UXLC corrections"
PAGE_HEADING = "Daniel Holman's suggested UXLC corrections"
INDEX_PAGE = "index.html"
INDEX_NAV_LABEL = "Index"
KETIV_QERE_PAGE = "table_data_findings.html"
KETIV_QERE_NAV_LABEL = "Ketiv/qere review"
SUPPRESSED_PAGE = "table_data_findings_suppressed.html"
SUPPRESSED_NAV_LABEL = "Suppressed"
THIS_NAV_LABEL = "UXLC corrections"

INTRO_PARAGRAPHS = (
    "Daniel Holman has been sending Chris Kimball and Ben Denckla suggested"
    " corrections to the UXLC, a book at a time, and this page collects them."
    " Most are places where he reads the Leningrad Codex images differently from"
    " the text as it stands; the rest ask the UXLC for a note on a reading Holman"
    ' and the UXLC agree about, and the "What Holman asks for" column below'
    " counts each kind.",
    "Each card is one case, and its labelled lines are Holman's, quoted from the"
    " email exactly as he wrote them, including his spellings of the accent"
    " names. One thing on a card is added rather than quoted: on the line giving"
    " the manuscript image, the folio link and the Internet Archive link after"
    " Holman's citation are decoded here from the page ordinal that citation"
    " begins with, so the folio number is not Holman's either.",
    # uxlc_comments holds no entries yet, so no card has a commentary section.
    # When the first one lands, add to the sentence below: "; the commentary
    # section on a card is a reader's remark and carries no more weight than
    # that".
    "Nothing here is a decision. The suggestions are Chris Kimball's to accept or"
    " decline for the UXLC.",
)


@dataclass(frozen=True)
class RenderedCase:
    number: int
    case: CorrectionCase
    image_hrefs: list[tuple[str, str, int, int]]


def render_uxlc_corrections_html(
    *,
    emails_dir: Path,
    output_html_path: Path,
    image_dir: Path,
    assets_dir: Path,
    json_output_path: Path,
) -> dict[str, object]:
    emails, cases = read_emails(emails_dir, image_dir)
    require_full_coverage([case.ref.key for case in cases])
    _require_commented_cases_exist(cases)

    rendered = _rendered_cases(cases, image_dir, output_html_path)
    _write_assets(
        assets_dir=assets_dir,
        output_html_path=output_html_path,
        filter_ids=all_filter_ids(cases, emails),
    )
    _write_page(
        emails=emails,
        cases=cases,
        rendered=rendered,
        output_html_path=output_html_path,
    )
    return _write_json(
        emails=emails,
        rendered=rendered,
        json_output_path=json_output_path,
    )


def _require_commented_cases_exist(cases: list[CorrectionCase]) -> None:
    known = {case.ref.key for case in cases}
    unmatched = sorted(set(COMMENTS_BY_REF) - known)
    if unmatched:
        raise ValueError(
            "uxlc_comments names cases that no email contains: "
            f"{unmatched}. Case keys look like {sorted(known)[0]!r}."
        )


def _rendered_cases(
    cases: list[CorrectionCase], image_dir: Path, output_html_path: Path
) -> list[RenderedCase]:
    """Pair each case with its images' hrefs, captions and pixel dimensions.

    The images are already on disk, written by the ingest step and tracked;
    this only reads each one's size so the markup can reserve its space and a
    #caseNN link lands on a target that does not then drift.
    """
    rendered: list[RenderedCase] = []
    for number, case in enumerate(cases, start=1):
        hrefs: list[tuple[str, str, int, int]] = []
        for image in case.images:
            path = image_dir / image.file_name
            width, height = _png_size(path)
            hrefs.append(
                (relative_href(path, output_html_path), image.caption, width, height)
            )
        rendered.append(RenderedCase(number=number, case=case, image_hrefs=hrefs))
    return rendered


def _png_size(path: Path) -> tuple[int, int]:
    """Width and height straight out of the PNG's IHDR chunk.

    Read by hand because this repo's venv deliberately has no Pillow, and the
    two numbers sit at a fixed offset in every PNG.
    """
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def _write_assets(
    *, assets_dir: Path, output_html_path: Path, filter_ids: list[str]
) -> None:
    colour_rules = "\n".join(
        f".cat-{filter_id} {{ background: {PALETTE[index % len(PALETTE)]}; }}"
        for index, filter_id in enumerate(filter_ids)
    )
    css_text = (assets_dir / "uxlc_corrections.css").read_text(encoding="utf-8")
    css_text = css_text.replace("/* __FILTER_COLORS__ */", colour_rules)
    output_html_path.with_suffix(".css").write_text(
        css_text, encoding="utf-8", newline=""
    )
    output_html_path.with_suffix(".js").write_text(
        (assets_dir / "uxlc_corrections.js").read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="",
    )


def _write_page(
    *,
    emails: list[SourceEmail],
    cases: list[CorrectionCase],
    rendered: list[RenderedCase],
    output_html_path: Path,
) -> None:
    email_by_key = {source_email.key: source_email for source_email in emails}
    cards = "\n".join(
        case_card_html(
            case_number=item.number,
            case=item.case,
            source_email=email_by_key[item.case.email_key],
            image_hrefs=item.image_hrefs,
            comment_entries=comments_for_ref(item.case.ref.key),
        )
        for item in rendered
    )
    intro = "\n".join(f"<p>{escape(text)}</p>" for text in INTRO_PARAGRAPHS)
    css_href = escape(output_html_path.with_suffix(".css").name)
    js_src = escape(output_html_path.with_suffix(".js").name)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(PAGE_TITLE)}</title>
<link rel="stylesheet" href="{css_href}">
</head>
<body>
<nav class="top-nav">
<a class="nav-link" href="{INDEX_PAGE}">{INDEX_NAV_LABEL}</a>
<a class="nav-link active" href="{escape(output_html_path.name)}">{THIS_NAV_LABEL}</a>
<a class="nav-link" href="{KETIV_QERE_PAGE}">{KETIV_QERE_NAV_LABEL}</a>
<a class="nav-link" href="{SUPPRESSED_PAGE}">{SUPPRESSED_NAV_LABEL}</a>
</nav>
<h1>{escape(PAGE_HEADING)}</h1>
<div class="intro">
{intro}
</div>
{_meta_grid_html(cases, emails)}
{summary_html(cases, emails)}
<h2 class="section-title">Cases</h2>
<div class="records">
{cards}
</div>
{_emails_section_html(emails, rendered)}
<script src="{js_src}" defer></script>
</body>
</html>
"""
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(html, encoding="utf-8", newline="")


def _meta_grid_html(cases: list[CorrectionCase], emails: list[SourceEmail]) -> str:
    books = len({case.ref.book for case in cases})
    boxes = (
        ("Cases", str(len(cases))),
        ("Source emails", str(len(emails))),
        ("Books", str(books)),
        ("Visible/Filtered-out", str(len(cases)) + "/0"),
    )
    rendered = "\n".join(
        (
            '<div class="meta-box">\n'
            f'<div class="meta-label">{escape(label)}</div>\n'
            + (
                '<div class="meta-value" id="visible-filtered-count">'
                if label == "Visible/Filtered-out"
                else '<div class="meta-value">'
            )
            + f"{escape(value)}</div>\n</div>"
        )
        for label, value in boxes
    )
    return f'<div class="meta-grid">\n{rendered}\n</div>'


def _emails_section_html(
    emails: list[SourceEmail], rendered: list[RenderedCase]
) -> str:
    blocks: list[str] = []
    for source_email in emails:
        cases_here = [
            item for item in rendered if item.case.email_key == source_email.key
        ]
        case_links = ", ".join(
            f'<a class="case-link" href="#{case_fragment_id(item.number)}">'
            f"#{item.number}</a>"
            for item in cases_here
        )
        preamble = "\n".join(
            f"<p>{inline_text_html(line)}</p>" for line in source_email.preamble
        )
        closing = "\n".join(
            f"<p>{inline_text_html(line)}</p>" for line in source_email.closing
        )
        # A message stays visible under any filter that keeps one of its cases,
        # so filtering by book does not empty this section.
        filter_ids = sorted(
            {email_filter_id(source_email.key)}
            | {
                filter_id
                for item in cases_here
                for filter_id in case_filter_ids(item.case)
            }
        )
        blocks.append(
            f'<article class="source-email" id="{email_fragment_id(source_email.key)}"'
            f' data-filter-ids="{escape(" ".join(filter_ids))}">\n'
            f"<h3>{escape(source_email.subject)}</h3>\n"
            f'<p class="email-headers">{escape(source_email.sender_name)}, '
            f"{escape(source_email.date_display)}"
            f" &middot; {len(cases_here)} case"
            f"{'' if len(cases_here) == 1 else 's'}: {case_links}</p>\n"
            f'<div class="email-prose">\n{preamble}\n{closing}\n</div>\n'
            f'<p class="email-file">Source: <code>'
            f"{escape(source_email.source_file_name)}</code></p>\n"
            "</article>"
        )
    return (
        '<h2 class="section-title">Source emails</h2>\n'
        '<p class="section-note">The greeting and sign-off of each message, with its'
        " cases linked. The body of every case is on its card above. Email"
        f" addresses are replaced with {escape(ADDRESS_REDACTION)}; nothing else"
        " is edited. The date is the date of the message itself, so the one"
        " forwarded to supply attachments left off a first send carries the"
        " forwarding date, and the original send time stands in the forwarded"
        " header quoted below it.</p>\n"
        '<div class="source-emails">\n' + "\n".join(blocks) + "\n</div>"
    )


def _write_json(
    *,
    emails: list[SourceEmail],
    rendered: list[RenderedCase],
    json_output_path: Path,
) -> dict[str, object]:
    payload = {
        "source_emails": [
            {
                "key": source_email.key,
                "source_file_name": source_email.source_file_name,
                "subject": source_email.subject,
                "from": source_email.sender_name,
                "date": source_email.date_iso,
                "preamble": list(source_email.preamble),
                "closing": list(source_email.closing),
            }
            for source_email in emails
        ],
        "cases": [
            {
                "case_number": item.number,
                "ref": item.case.ref.key,
                "book": item.case.ref.book,
                "book_display": book_display_name(item.case.ref.book),
                "chapter": item.case.ref.chapter,
                "verse": item.case.ref.verse,
                "atom": item.case.ref.atom,
                "email_key": item.case.email_key,
                "index_in_email": item.case.index_in_email,
                "heading": item.case.heading,
                "suggestion_kind": SUGGESTION_KIND_LABELS[
                    suggestion_kind(item.case.ref.key)
                ],
                "fields": [
                    {"label": label, "value": value}
                    for label, value in item.case.fields
                ],
                "manuscript_folio": _folio_or_none(item.case.image_location),
                "images": [
                    {
                        "attachment": image.source_filename,
                        "caption": image.caption,
                        "file": image.file_name,
                    }
                    for image in item.case.images
                ],
            }
            for item in rendered
        ],
    }
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="",
    )
    return {
        "email_count": len(emails),
        "case_count": len(rendered),
        "image_count": sum(len(item.image_hrefs) for item in rendered),
        "commented_case_count": sum(
            1 for item in rendered if comments_for_ref(item.case.ref.key)
        ),
    }


def _folio_or_none(image_location: str | None) -> str | None:
    if image_location is None:
        return None
    page = manuscript_page(image_location)
    return None if page is None else page.folio_label
