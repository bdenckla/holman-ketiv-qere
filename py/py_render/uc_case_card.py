"""Render one of Holman's suggestions as a card."""

from __future__ import annotations

from html import escape
import os
from pathlib import Path

from py_render.rt_html_utils import external_link_html, record_category_badge_html
from py_render.uc_comments import comments_html
from py_render.uc_hebrew_runs import inline_text_html
from python_modules.uxlc_atom_locations import AtomLocation
from python_modules.uxlc_change_records import change_record_links
from python_modules.uxlc_email_extract import (
    CorrectionCase,
    FIRST_FIELD_LABELS,
    IMAGE_LOCATION_LABELS,
    KNOWN_FIELD_LABELS,
    SourceEmail,
    book_slug,
)
from python_modules.uxlc_external_links import book_display_name, verse_links
from python_modules.uxlc_manuscript_page import manuscript_page, manuscript_position

# The labels are Holman's, verbatim from his emails, and the parser keeps them
# that way. These two are relabelled for display only: the page says
# "suggestion" where it has the choice, and "Corrected Text" and "Suggested
# Correction" are the two labels where it has one.
DISPLAY_FIELD_LABELS = {
    "Corrected Text": "Suggested Text",
    "Suggested Correction": "Suggestion",
}

# Holman spells the image-location label three ways, and the value under it is
# no longer his citation but an estimate derived here, so the three collapse to
# one label of our own.
MANUSCRIPT_LOCATION_LABEL = "Manuscript location"

# The order the fields are shown in. This is the message's own order with ONE
# field moved: Holman writes the current text, then where he read it, then what
# he proposes, then the resulting text, and Ben asked on 2026-08-11 for the
# current text and the suggested text next to each other. So the suggested text
# moves up to sit under the current one, and nothing else moves.
#
# Do not tidy this into a "sensible" order. A first pass also moved the
# manuscript location below the suggestion, which reads well enough and was not
# asked for; Ben's reply the same day was that the card changes "seemed to go
# way beyond what I asked". The nine cases whose message has no Corrected Text
# field are therefore shown in exactly their message order.
_FIELD_ORDER = (
    *FIRST_FIELD_LABELS,
    "Corrected Text",
    *sorted(IMAGE_LOCATION_LABELS),
    "Suggested Correction",
    "Critical Note",
    "Note",
)
_FIELD_RANK = {label: rank for rank, label in enumerate(_FIELD_ORDER)}
_UNRANKED_LABELS = KNOWN_FIELD_LABELS - set(_FIELD_RANK)
if _UNRANKED_LABELS:
    raise AssertionError(
        f"no display rank for the field labels {sorted(_UNRANKED_LABELS)}; add "
        "them to _FIELD_ORDER, which decides what a card shows first"
    )


def case_fragment_id(case_number: int) -> str:
    return f"case{case_number:02d}"


def book_filter_id(book: str) -> str:
    return f"book-{book_slug(book)}"


def email_fragment_id(email_key: str) -> str:
    return f"src-{email_key}"


def case_filter_ids(case: CorrectionCase) -> tuple[str, ...]:
    return (book_filter_id(case.ref.book),)


def case_card_html(
    *,
    case_number: int,
    case: CorrectionCase,
    source_email: SourceEmail,
    location: AtomLocation,
    image_hrefs: list[tuple[str, str, int, int]],
    comment_entries: tuple[dict[str, object], ...],
) -> str:
    fragment_id = case_fragment_id(case_number)
    filter_ids = case_filter_ids(case)
    badges = record_category_badge_html(
        filter_id=book_filter_id(case.ref.book),
        label=book_display_name(case.ref.book),
    )
    fields = _fields_html(case, location)
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
    return f"{escape(reference)}\n{links}\n{_change_record_links_html(case)}"


def _change_record_links_html(case: CorrectionCase) -> str:
    """The change list's records for this case, or nothing when it has none.

    Labelled with the record's own id, which is the date it was entered and its
    sequence number within that date, so the Judges record's April date shows
    on the link that it is older than the message the card quotes.
    """
    return "\n".join(
        external_link_html(
            href=link.href, label=f"Change {link.record_id}", title=link.title
        )
        for link in change_record_links(case.ref.key)
    )


def _fields_html(case: CorrectionCase, location: AtomLocation) -> str:
    ordered = sorted(case.fields, key=lambda field: _FIELD_RANK[field[0]])
    return "\n".join(
        (
            _field_html(
                MANUSCRIPT_LOCATION_LABEL, _manuscript_location_html(value, location)
            )
            if label in IMAGE_LOCATION_LABELS
            else _field_html(
                DISPLAY_FIELD_LABELS.get(label, label), inline_text_html(value)
            )
        )
        for label, value in ordered
    )


def _field_html(label: str, value_html: str) -> str:
    return (
        f'<div class="case-field">\n'
        f"<dt>{escape(label)}</dt>\n"
        f"<dd>{value_html}</dd>\n"
        f"</div>"
    )


def _manuscript_location_html(image_location: str, location: AtomLocation) -> str:
    """The estimated column and line, with Holman's column where it differs.

    Holman's citation names the scan file he worked from and puts the atom in a
    band of a column of it. The file name says nothing a reader can use, so it
    is not shown; the column is a discrete fact the estimate states too, so the
    two are compared, and his reading is given whenever they disagree. The band
    is not compared: top, middle and bottom are a gloss that a line number
    supersedes, and testing them against equal nine-line thirds would report
    disagreements a line wide as real ones.
    """
    text = f"Column {location.column}, line {location.rounded_line} or thereabouts."
    holman = manuscript_position(image_location)
    if holman is not None and holman.column != location.column:
        text += f" Holman gives {holman.display}."
    return escape(text) + _folio_link_html(image_location)


def _folio_link_html(image_location: str) -> str:
    """The Sefaria image of the leaf, decoded from Holman's page ordinal."""
    page = manuscript_page(image_location)
    if page is None:
        return ""
    link = external_link_html(
        href=page.sefaria_image_url, label=f"folio {page.folio_label}"
    )
    return f'\n<span class="folio-links">{link}</span>'


def _images_html(image_hrefs: list[tuple[str, str, int, int]]) -> str:
    """The attached crops, uncaptioned.

    The caption Holman's filenames carry stays in the data and reaches the alt
    attribute, which is not what a caption is: it is read only where the image
    itself cannot be seen, so it is not the clutter on every card that the
    visible caption was.
    """
    if not image_hrefs:
        return '<p class="no-image">No image attached</p>'
    figures = "\n".join(
        (
            "<figure>\n"
            f'<a href="{escape(href)}" target="_blank" rel="noopener">'
            f'<img class="image-thumb" src="{escape(href)}"'
            f' width="{width}" height="{height}" loading="lazy" decoding="async"'
            f' alt="{escape(caption)}"></a>\n'
            "</figure>"
        )
        for href, caption, width, height in image_hrefs
    )
    return f'<div class="image-strip">\n{figures}\n</div>'


def relative_href(asset_path: Path, output_html_path: Path) -> str:
    return os.path.relpath(asset_path, output_html_path.parent).replace("\\", "/")
