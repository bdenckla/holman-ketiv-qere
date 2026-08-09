"""Resolve Holman's manuscript-image citations to Leningrad Codex folios.

Holman cites the page he worked from as, for example,
``069_Exo_7.9b-8.3a / Col. 2 middle``. The leading number is a 1-based ordinal
over page sides, counting folio 001A as 1, so

    ordinal = 2 * folio + (0 for side A, 1 for side B) - 1

and the folio and side invert out of it. The three-letter code names the book
the page starts in, which is not always the book of the case on it, so it is
shown but not checked.

Checked 2026-08-08: inverting all twenty ordinals in ``emails/`` and looking the
folios up in the sibling ``codex-index-leningrad``'s
``UXLC-utils-sparse/data/lci_recs.json`` reproduced Holman's verse range in
every one. That file is derived from tanach.us's ``LCIndex.xml``, the UXLC page
index, which is presumably where Holman's ordinals come from too. To
re-establish the check, decode an ordinal here and compare against the
``page`` row of that JSON.

The two image URLs follow ``codex-index-leningrad/lenin-wiki/py/image_urls.py``,
whose Internet Archive page number is ``2 * folio + side - 2``, i.e. exactly one
less than Holman's ordinal.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

_LOCATION_RE = re.compile(r"^(?P<ordinal>\d{2,4})_(?P<book_code>[A-Za-z0-9]+)_")
_SEFARIA_PREFIX = "https://manuscripts.sefaria.org/leningrad-color/"
_ARCHIVE_PREFIX = "https://archive.org/details/Leningrad_Codex_Color_Images/page/"


@dataclass(frozen=True)
class ManuscriptPage:
    ordinal: int
    folio: int
    side: str
    book_code: str

    @property
    def folio_label(self) -> str:
        """The folio in the DDDA form the image URLs use, e.g. 035A."""
        return f"{self.folio:03d}{self.side}"

    @property
    def sefaria_image_url(self) -> str:
        return f"{_SEFARIA_PREFIX}BIB_LENCDX_F{self.folio_label}.jpg"

    @property
    def archive_page_url(self) -> str:
        return f"{_ARCHIVE_PREFIX}n{self.ordinal - 1}/mode/1up?view=theater"


def manuscript_page(image_location: str) -> ManuscriptPage | None:
    """Decode a manuscript-image citation, or None when it has no ordinal."""
    match = _LOCATION_RE.match(image_location.strip())
    if match is None:
        return None
    ordinal = int(match.group("ordinal"))
    if ordinal < 1:
        raise ValueError(f"manuscript page ordinal out of range: {image_location!r}")
    # ordinal + 1 == 2 * folio + side, with side 0 for A and 1 for B.
    folio, side = divmod(ordinal + 1, 2)
    return ManuscriptPage(
        ordinal=ordinal,
        folio=folio,
        side="A" if side == 0 else "B",
        book_code=match.group("book_code"),
    )
