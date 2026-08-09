"""What each of Holman's suggestions asks the UXLC to do.

This is the one editorial layer on the page: everything else is the emails'
wording. The four values read Holman's "Suggested Correction" line and say
whether it asks for a change to the text, for an apparatus note, for both, or
offers the two as alternatives -- which is the question the UXLC's editor has to
answer first, and the one thing a reader cannot see at a glance from twenty
cards.

Classifying by keyword would be guesswork over prose, so the table is written
out. Every case must appear in it: ``require_full_coverage`` raises on a case
with no entry and on an entry naming no case, so a new email cannot arrive and
quietly land in no category.
"""

from __future__ import annotations

CHANGE = "change"
CHANGE_AND_NOTE = "change-and-note"
CHANGE_OR_NOTE = "change-or-note"
NOTE = "note"

SUGGESTION_KIND_LABELS = {
    CHANGE: "Change the text",
    CHANGE_AND_NOTE: "Change the text and add a note",
    CHANGE_OR_NOTE: "Change the text or add a note",
    NOTE: "Add or revise a note",
}
SUGGESTION_KIND_ORDER = (CHANGE, CHANGE_AND_NOTE, CHANGE_OR_NOTE, NOTE)

# Keyed as uxlc_email_extract.CaseRef.key spells a reference: bk39 book id,
# chapter:verse.atom. Leviticus is Levit and Deuteronomy is Deuter there.
SUGGESTION_KIND_BY_REF = {
    "Exodus 7:20.19": CHANGE_OR_NOTE,
    "Exodus 11:6.1": CHANGE_OR_NOTE,
    "Exodus 20:3.2": CHANGE_OR_NOTE,
    "Exodus 38:12.6": CHANGE_OR_NOTE,
    "Levit 7:25.6": NOTE,
    # "Replace Tevir with Mereka and place note on blemish on MS"
    "Levit 15:8.2": CHANGE_AND_NOTE,
    "Levit 16:21.6": NOTE,
    # "Remove Mahpakh and revise note"
    "Levit 25:20.4": CHANGE_AND_NOTE,
    "Deuter 33:28.13": CHANGE_OR_NOTE,
    "Joshua 5:1.36": CHANGE,
    "Joshua 9:23.10": CHANGE,
    "Joshua 19:8.8": CHANGE,
    "Joshua 20:4.12": CHANGE,
    "Judges 11:24.7": CHANGE,
    "1Samuel 7:10.10": CHANGE,
    "1Samuel 13:4.11": CHANGE,
    "2Samuel 5:21.1": CHANGE,
    "2Samuel 7:22.7": NOTE,
    "2Samuel 15:26.11": NOTE,
    "2Samuel 24:10.19": CHANGE,
}


def suggestion_kind(ref_key: str) -> str:
    kind = SUGGESTION_KIND_BY_REF.get(ref_key)
    if kind is None:
        raise ValueError(
            f"no suggestion kind for {ref_key!r}; add it to "
            "python_modules/uxlc_case_tags.SUGGESTION_KIND_BY_REF"
        )
    return kind


def require_full_coverage(ref_keys: list[str]) -> None:
    present = set(ref_keys)
    for ref_key in ref_keys:
        suggestion_kind(ref_key)
    unmatched = sorted(set(SUGGESTION_KIND_BY_REF) - present)
    if unmatched:
        raise ValueError(
            "SUGGESTION_KIND_BY_REF names cases that no email contains: " f"{unmatched}"
        )
