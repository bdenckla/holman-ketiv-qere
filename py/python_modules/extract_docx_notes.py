from __future__ import annotations

from typing import cast
import re

from pycmn import bib_locales

VERSE_PATTERN = re.compile(
    r"^(?P<book_token>.*) (?P<chapter>\d+):(?P<verse>\d+)\.(?P<segment>\d+)$"
)

STANDARD_BOOK_NAME_BY_ABBREVIATION = {
    "1Ch": bib_locales.BK_FST_CHR,
    "1Ki": bib_locales.BK_FST_KGS,
    "1Sa": bib_locales.BK_FST_SAM,
    "2Ch": bib_locales.BK_SND_CHR,
    "2Ki": bib_locales.BK_SND_KGS,
    "2Sa": bib_locales.BK_SND_SAM,
    "Eze": bib_locales.BK_EZEKIEL,
    "Isa": bib_locales.BK_ISAIAH,
    "Jer": bib_locales.BK_JEREM,
    "Job": bib_locales.BK_JOB,
    "Josh": bib_locales.BK_JOSHUA,
    "Judg": bib_locales.BK_JUDGES,
    "Prov": bib_locales.BK_PROV,
    "Ps": bib_locales.BK_PSALMS,
    "Zeph": bib_locales.BK_TSEF,
}

NOTES_JUNK_REPLACEMENTS = (
    ("y\u202c\u200f", ""),
    ("\u202c\u202c", ""),
)

# Strip known invisible format marks before pattern counting.
INVISIBLE_MARK_PATTERN = re.compile(r"[\u034F\u200C-\u200F\u202A-\u202E\u2066-\u2069]")
HEBREW_RUN_PATTERN = re.compile(r"[\u0590-\u05FF\uFB1D-\uFB4F]+")
NOTES_PREFIX = "MAM - No Comments | UXLC - "
HAKETER_SEPARATOR = " | HaKeter - "
UXLC_YATIR_PATTERN = re.compile(r"^(?P<uxlc>.*)\n\((?P<yatir>[^)]+)\)$", re.DOTALL)

ALLOWED_LENINGRAD_TEXT_VALUES = {"", "’"}


def parse_verse_reference(verse: str) -> tuple[str, str, str, str]:
    match = VERSE_PATTERN.fullmatch(verse)
    if match is None:
        raise ValueError(f"unexpected verse format: {verse!r}")
    return (
        match.group("book_token"),
        match.group("chapter"),
        match.group("verse"),
        match.group("segment"),
    )


def verse_book_name(verse: str) -> str:
    book_token, *_ = parse_verse_reference(verse)
    return standard_book_name(book_token)


def standard_book_name(book_token: str) -> str:
    mapped = STANDARD_BOOK_NAME_BY_ABBREVIATION.get(book_token)
    if mapped is not None:
        return mapped

    try:
        bib_locales.bk24id(book_token)
    except KeyError as exc:
        raise ValueError(f"unknown verse book token: {book_token!r}") from exc
    return book_token


def standardize_verse_book_name(verse: str) -> str:
    book_token, chapter, verse_num, segment = parse_verse_reference(verse)
    return f"{standard_book_name(book_token)} {chapter}:{verse_num}.{segment}"


def strip_known_notes_junk(notes: str) -> str:
    for old, new in NOTES_JUNK_REPLACEMENTS:
        notes = notes.replace(old, new)
    return notes


def clean_notes_formatting_artifacts(notes: str) -> str:
    return INVISIBLE_MARK_PATTERN.sub("", strip_known_notes_junk(notes))


def abstract_hebrew_runs(text: str) -> str:
    return HEBREW_RUN_PATTERN.sub("<HEB>", text)


def split_notes_components(notes: str) -> tuple[str, str | None, str | None]:
    normalized_notes = clean_notes_formatting_artifacts(notes)
    if not normalized_notes.startswith(NOTES_PREFIX):
        raise ValueError(f"unexpected notes format: {notes!r}")

    body = normalized_notes.removeprefix(NOTES_PREFIX)
    haketer_text = None
    if HAKETER_SEPARATOR in body:
        uxlc_text, haketer_text = body.split(HAKETER_SEPARATOR, 1)
    else:
        uxlc_text = body

    yatir = None
    uxlc_match = UXLC_YATIR_PATTERN.fullmatch(uxlc_text)
    if uxlc_match is not None:
        uxlc_text = uxlc_match.group("uxlc")
        yatir = uxlc_match.group("yatir")

    uxlc_text = uxlc_text.strip()
    if not uxlc_text:
        raise ValueError(f"unexpected empty UXLC notes component: {notes!r}")

    if haketer_text is not None:
        haketer_text = haketer_text.strip()
        if not haketer_text:
            raise ValueError(f"unexpected empty HaKeter notes component: {notes!r}")

    return (uxlc_text, yatir.strip() if yatir is not None else None, haketer_text)


def notes_structured_signature(notes: str) -> tuple[str, str | None, str | None]:
    notes_uxlc, notes_uxlc_yatir, notes_haketer = split_notes_components(notes)
    return (
        abstract_hebrew_runs(notes_uxlc),
        notes_uxlc_yatir,
        abstract_hebrew_runs(notes_haketer) if notes_haketer is not None else None,
    )


def fix_row_37_notes(notes: str) -> str:
    expected_notes = "MAM - No Comments | UXLC - מַה־לִּי־פֹה֙ מי־לי־"
    if notes != expected_notes:
        return notes

    fixed_notes = notes.replace("פֹה֙", "")
    parts = fixed_notes.split(" ")
    if len(parts) != 9:
        raise ValueError(f"unexpected row 37 notes tokenization: {fixed_notes!r}")

    # After stripping פֹה֙, the ketiv and qere land in reverse order.
    parts[7], parts[8] = parts[8], parts[7]
    return " ".join(parts)


def fix_row_2_notes(notes: str) -> str:
    buggy_qere = "הֶהָלְכ֣וְּּ"
    fixed_qere = "הֶהָלְכ֣וּ"
    if buggy_qere not in notes:
        return notes
    return notes.replace(buggy_qere, fixed_qere)


def apply_notes_fixes(row_data: dict[str, object]) -> None:
    row_number = cast(int, row_data["row_number"])
    if row_number == 37 and row_data.get("word") == "":
        row_data["word"] = "מַה־לִּי־"

    current_notes = row_data.get("notes")
    if not isinstance(current_notes, str):
        return

    cleaned_notes = clean_notes_formatting_artifacts(current_notes)
    fixed_notes = cleaned_notes
    targeted_fix_applied = False

    if row_number == 2:
        updated_notes = fix_row_2_notes(fixed_notes)
        targeted_fix_applied = updated_notes != fixed_notes
        fixed_notes = updated_notes

    if row_number == 37:
        updated_notes = fix_row_37_notes(fixed_notes)
        targeted_fix_applied = targeted_fix_applied or updated_notes != fixed_notes
        fixed_notes = updated_notes

    if fixed_notes == current_notes:
        return

    if targeted_fix_applied:
        row_data["notes_orig"] = cleaned_notes
    row_data["notes"] = fixed_notes


def assert_text_columns_before_drop(row_data: dict[str, object]) -> int:
    row_number = row_data["row_number"]

    entry_text = row_data.get("entry")
    if not isinstance(entry_text, str):
        raise ValueError(f"unexpected entry type at row {row_number}: {entry_text!r}")
    expected_entry = str(row_number)
    if entry_text != expected_entry:
        raise ValueError(
            f"unexpected entry text at row {row_number}: expected {expected_entry!r}, got {entry_text!r}"
        )

    aleppo_text = row_data.get("aleppo")
    if not isinstance(aleppo_text, str):
        raise ValueError(f"unexpected aleppo type at row {row_number}: {aleppo_text!r}")
    if aleppo_text != "":
        raise ValueError(
            f"unexpected non-empty aleppo text at row {row_number}: {aleppo_text!r}"
        )

    leningrad_text = row_data.get("leningrad")
    if not isinstance(leningrad_text, str):
        raise ValueError(
            f"unexpected leningrad type at row {row_number}: {leningrad_text!r}"
        )
    if leningrad_text not in ALLOWED_LENINGRAD_TEXT_VALUES:
        raise ValueError(
            f"unexpected leningrad text at row {row_number}: {leningrad_text!r}"
        )
    return 1 if leningrad_text == "’" else 0
