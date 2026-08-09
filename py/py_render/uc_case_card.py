"""Render one suggested correction as a card."""

from __future__ import annotations

from html import escape
import os
from pathlib import Path

from py_render.rt_html_utils import external_link_html, record_category_badge_html
from py_render.uc_comments import comments_html
from py_render.uc_hebrew_runs import inline_text_html
from python_modules.uxlc_case_tags import (
    SUGGESTION_KIND_LABELS,
    suggestion_kind,
)
from python_modules.uxlc_email_extract import (
    CorrectionCase,
    IMAGE_LOCATION_LABELS,
    SourceEmail,
    book_slug,
)
from python_modules.uxlc_external_links import book_display_name, verse_links
from python_modules.uxlc_manuscript_page import manuscript_page


def case_fragment_id(case_number: int) -> str:
    return f"case{case_number:02d}"


def book_filter_id(book: str) -> str:
    return f"book-{book_slug(book)}"


def kind_filter_id(kind: str) -> str:
    return f"kind-{kind}"


def email_filter_id(email_key: str) -> str:
    return f"email-{email_key}"


def email_fragment_id(email_key: str) -> str:
    return f"src-{email_key}"


def case_filter_ids(case: CorrectionCase) -> tuple[str, ...]:
    return (
        book_filter_id(case.ref.book),
        kind_filter_id(suggestion_kind(case.ref.key)),
        email_filter_id(case.email_key),
    )


def case_card_html(
    *,
    case_number: int,
    case: CorrectionCase,
    source_email: SourceEmail,
    image_hrefs: list[tuple[str, str, int, int]],
    comment_entries: tuple[dict[str, object], ...],
) -> str:
    fragment_id = case_fragment_id(case_number)
    kind = suggestion_kind(case.ref.key)
    filter_ids = case_filter_ids(case)
    badges = "\n".join(
        (
            record_category_badge_html(
                filter_id=book_filter_id(case.ref.book),
                label=book_display_name(case.ref.book),
            ),
            record_category_badge_html(
                filter_id=kind_filter_id(kind), label=SUGGESTION_KIND_LABELS[kind]
            ),
        )
    )
    fields = "\n".join(_field_html(label, value) for label, value in case.fields)
    provenance = (
        '<p class="case-source">Holman\'s case '
        f"{case.index_in_email} in "
        f'<a href="#{email_fragment_id(case.email_key)}">'
        f"{escape(source_email.subject)}</a>, "
        f"{escape(source_email.date_display)}.</p>"
    )
    return f"""<article
id="{fragment_id}"
class="record-card"
data-filter-ids="{escape(' '.join(filter_ids))}"
>
<div class="record-head">
<a class="record-ref" href="#{fragment_id}">#{case_number}</a>
<span class="record-verse">{_verse_ref_html(case)}</span>
<span class="category-badges">
{badges}
</span>
</div>
<div class="record-grid">
<div>
<dl class="case-fields">
{fields}
</dl>
{provenance}
</div>
<div class="image-panel">
<div class="image-caption">Holman's images</div>
{_images_html(image_hrefs)}
</div>
</div>
{comments_html(comment_entries)}
</article>"""


def _verse_ref_html(case: CorrectionCase) -> str:
    ref = case.ref
    reference = (
        f"{book_display_name(ref.book)} {ref.chapter}:{ref.verse}, atom {ref.atom}"
    )
    links = "\n".join(
        external_link_html(href=link.href, label=link.label, title=link.title)
        for link in verse_links(ref.book, ref.chapter, ref.verse)
    )
    return f"{escape(reference)}\n{links}"


def _field_html(label: str, value: str) -> str:
    value_html = inline_text_html(value)
    if label in IMAGE_LOCATION_LABELS:
        value_html += _manuscript_page_links_html(value)
    return (
        f'<div class="case-field">\n'
        f"<dt>{escape(label)}</dt>\n"
        f"<dd>{value_html}</dd>\n"
        f"</div>"
    )


def _manuscript_page_links_html(image_location: str) -> str:
    page = manuscript_page(image_location)
    if page is None:
        return ""
    links = "\n".join(
        (
            external_link_html(
                href=page.sefaria_image_url, label=f"folio {page.folio_label}"
            ),
            external_link_html(href=page.archive_page_url, label="Internet Archive"),
        )
    )
    return f'\n<span class="folio-links">{links}</span>'


def _images_html(image_hrefs: list[tuple[str, str, int, int]]) -> str:
    if not image_hrefs:
        return '<p class="no-image">No image attached</p>'
    figures = "\n".join(
        (
            "<figure>\n"
            f'<a href="{escape(href)}" target="_blank" rel="noopener">'
            f'<img class="image-thumb" src="{escape(href)}"'
            f' width="{width}" height="{height}" loading="lazy" decoding="async"'
            f' alt="{escape(caption)}"></a>\n'
            f"<figcaption>{escape(caption)}</figcaption>\n"
            "</figure>"
        )
        for href, caption, width, height in image_hrefs
    )
    return f'<div class="image-strip">\n{figures}\n</div>'


def relative_href(asset_path: Path, output_html_path: Path) -> str:
    return os.path.relpath(asset_path, output_html_path.parent).replace("\\", "/")
