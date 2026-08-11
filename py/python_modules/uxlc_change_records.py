"""Where each of Holman's cases turns up in the UXLC's proposed-changes list.

The UXLC's editor publishes the changes proposed for the next release as one
long page, at ``CHANGES_PAGE_URL``. It is a flat chronological list rather than
a per-book one, and a record's anchor is the date it was entered plus its
sequence number within that date -- ``#2026.08.05-6`` -- so nothing in an anchor
says which verse the record is about. The mapping from a case to its records is
therefore written out here rather than derived.

Three things the table records that a derivation would have got wrong:

  * The change list numbers the atom differently from Holman in three cases.
    His Lev 16:21.6 is the list's Lev 16:21.7, his Lev 25:20.4 is its Lev
    25:20.3, and his Joshua 5:1 word 36 is its Josh 5:1.37. The word is the same
    one in each -- the same reading is quoted and the same correction described.

  * One case has two records, because the list splits it. Holman's Joshua 20:4
    case asks for the merkha and the meteg of זִקְנֵי־הָעִיר to change places,
    and the list enters that as one record per word, 2026.08.05-15 and -16.

  * The Judges record is not Holman's. 2026.04.10-7 is on the same word as his
    Judges 11:24 case and asks the same question about the same indistinct mark,
    but it was entered four months before his message and Ben Denckla is its
    author. It is linked because it is the change list's record for that word,
    which is what a reader of the card wants; it is not the disposition of
    Holman's message.

The six Samuel cases have no record in this list. That is what the list holds,
not a judgement about them.

The page is versioned by date, so a later one has a different URL. When it
appears, update ``CHANGES_PAGE_URL`` and re-read the ids: a record already
entered keeps its date-and-sequence id, but a case with no record yet may have
gained one.
"""

from __future__ import annotations

from dataclasses import dataclass

CHANGES_PAGE_URL = (
    "https://hcanat.us/Changes/2026.10.19%20-%20Changes/2026.10.19%20-%20Changes.html"
)
CHANGES_PAGE_LABEL = "2026.10.19 - Changes"
CHANGES_PAGE_DESCRIPTION = "the changes proposed for UXLC 2.6"

# Keyed as uxlc_email_extract.CaseRef.key spells a reference: bk39 book id,
# chapter:verse.atom. Leviticus is Levit and Deuteronomy is Deuter there. The
# values are the change list's own ids, which is what its anchors are.
CHANGE_RECORD_IDS_BY_REF = {
    "Exodus 7:20.19": ("2026.08.05-6",),
    "Exodus 11:6.1": ("2026.08.05-3",),
    "Exodus 20:3.2": ("2026.08.05-4",),
    "Exodus 38:12.6": ("2026.08.05-5",),
    "Levit 7:25.6": ("2026.08.05-7",),
    "Levit 15:8.2": ("2026.08.05-8",),
    # The list files this one as Lev 16:21.7.
    "Levit 16:21.6": ("2026.08.05-9",),
    # The list files this one as Lev 25:20.3.
    "Levit 25:20.4": ("2026.08.05-10",),
    "Deuter 33:28.13": ("2026.08.05-11",),
    # The list files this one as Josh 5:1.37.
    "Joshua 5:1.36": ("2026.08.05-12",),
    "Joshua 9:23.10": ("2026.08.05-13",),
    "Joshua 19:8.8": ("2026.08.05-14",),
    # Josh 20:4.12 is the merkha under the nun of זִקְנֵי־ and Josh 20:4.13 the
    # meteg under the ayin of הָעִיר, which is Holman's one case in two records.
    "Joshua 20:4.12": ("2026.08.05-15", "2026.08.05-16"),
    # Ben Denckla's, and four months older than Holman's message. See above.
    "Judges 11:24.7": ("2026.04.10-7",),
}


@dataclass(frozen=True)
class ChangeRecordLink:
    record_id: str
    href: str
    title: str


def change_record_links(ref_key: str) -> tuple[ChangeRecordLink, ...]:
    """The change list's records for one case, in the order it lists them."""
    return tuple(
        ChangeRecordLink(
            record_id=record_id,
            href=f"{CHANGES_PAGE_URL}#{record_id}",
            title=(
                f"Change item {record_id} in {CHANGES_PAGE_LABEL}, "
                f"{CHANGES_PAGE_DESCRIPTION}"
            ),
        )
        for record_id in CHANGE_RECORD_IDS_BY_REF.get(ref_key, ())
    )


def require_known_refs(ref_keys: list[str]) -> None:
    """Raise on a table entry naming no case, so a mistyped key is loud.

    There is no check the other way: a case with no entry is the ordinary state
    of one the change list has not reached.
    """
    unmatched = sorted(set(CHANGE_RECORD_IDS_BY_REF) - set(ref_keys))
    if unmatched:
        raise ValueError(
            "CHANGE_RECORD_IDS_BY_REF names cases that no email contains: "
            f"{unmatched}"
        )
