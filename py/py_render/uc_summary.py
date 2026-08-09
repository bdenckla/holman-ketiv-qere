"""The two filter columns above the cards: book, and kind of suggestion.

There was a third, by source email, until it was dropped: a message is one
book's worth of cases, so filtering by it did what the book column already did.
The messages themselves are still listed, in the page's Source emails section.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from html import escape

from mb_cmn import bib_locales as tbn
from py_render.uc_case_card import book_filter_id, kind_filter_id
from python_modules.uxlc_case_tags import (
    SUGGESTION_KIND_LABELS,
    SUGGESTION_KIND_ORDER,
    suggestion_kind,
)
from python_modules.uxlc_email_extract import CorrectionCase
from python_modules.uxlc_external_links import book_display_name


@dataclass(frozen=True)
class FilterRow:
    filter_id: str
    label: str
    count: int


def summary_html(cases: list[CorrectionCase]) -> str:
    groups = (
        ("Book", _book_rows(cases)),
        ("What Holman asks for", _kind_rows(cases)),
    )
    return (
        '<div class="summary-columns">\n'
        + "\n".join(_group_html(title, rows) for title, rows in groups)
        + "\n</div>"
    )


def all_filter_ids(cases: list[CorrectionCase]) -> list[str]:
    return [
        row.filter_id for rows in (_book_rows(cases), _kind_rows(cases)) for row in rows
    ]


def _book_rows(cases: list[CorrectionCase]) -> list[FilterRow]:
    counts = Counter(case.ref.book for case in cases)
    return [
        FilterRow(book_filter_id(book), book_display_name(book), counts[book])
        for book in sorted(counts, key=tbn.get_bknu)
    ]


def _kind_rows(cases: list[CorrectionCase]) -> list[FilterRow]:
    counts = Counter(suggestion_kind(case.ref.key) for case in cases)
    return [
        FilterRow(kind_filter_id(kind), SUGGESTION_KIND_LABELS[kind], counts[kind])
        for kind in SUGGESTION_KIND_ORDER
        if counts[kind]
    ]


def _group_html(title: str, rows: list[FilterRow]) -> str:
    row_html = "\n".join(
        (
            f'<tr data-filter-id="{escape(row.filter_id)}">\n'
            f'<td><span class="cat-swatch cat-{escape(row.filter_id)}"></span>'
            f"{escape(row.label)}</td>\n"
            f"<td>{row.count}</td>\n"
            "</tr>"
        )
        for row in rows
    )
    return (
        '<section class="summary-group">\n'
        f'<h2 class="summary-group-title">{escape(title)}</h2>\n'
        f'<table class="summary">\n{row_html}\n</table>\n'
        "</section>"
    )
