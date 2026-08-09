"""Daniel Holman's suggested-UXLC-correction emails, ingested and parsed.

Each message from Daniel Holman to Chris Kimball and Ben Denckla proposes
corrections to the UXLC. The body is a short preamble, a run of per-atom cases,
and a sign-off. A case is a heading line followed by ``Label: value`` lines; the
label vocabulary drifts from message to message (``Word / Verse`` in one,
``Current Text`` in another), so the labels are kept verbatim rather than
normalized, and the renderer shows the email's wording.

Two steps, because this repo is public and a .eml file's headers carry the
correspondents' addresses:

  ``ingest_eml_files``  reads the .eml files from a local, untracked mailbox and
    writes the tracked derivative: one address-redacted body text and one small
    metadata JSON per message, plus each attached PNG. Run it when a new message
    arrives; it is the only step that needs the mailbox.

  ``read_emails``  reads that derivative. This is what the report is generated
    from, so a fresh clone can regenerate the page without the .eml files.

One thing is read out of a body rather than read off it: a Latin note letter
Holman's mail client embedded inside a Hebrew word, with the bidi controls that
carry it. See ``_without_embedded_note_letter``.

Parsing is deliberately fail-fast: an unrecognized field label, whether inside
a case or in the position that would have opened one, a heading whose reference
disagrees with its first field, an attachment that cannot be assigned to a
case, and a duplicate reference all raise rather than dropping content. What is
assumed rather than checked is that a field value is one line, and that the
prose after a message's last case is its sign-off.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import email
import email.message
import email.policy
import email.utils
import json
from pathlib import Path
import re

from mb_cmn import bib_locales as tbn

# The first labelled line of every case carries one of these labels. A heading
# is recognized by being the prose line directly above such a label.
FIRST_FIELD_LABELS = (
    "Word / Verse",
    "Word/Verse",
    "Current UXLC",
    "Current Text",
)
OTHER_FIELD_LABELS = (
    "Manuscript Image",
    "Image Location",
    "UXLC Image Location",
    "Suggested Correction",
    "Corrected Text",
    "Critical Note",
    "Note",
)
KNOWN_FIELD_LABELS = frozenset(FIRST_FIELD_LABELS + OTHER_FIELD_LABELS)

# Labels whose value names the Leningrad Codex image and column Holman worked
# from, e.g. "069_Exo_7.9b-8.3a / Col. 2 middle".
IMAGE_LOCATION_LABELS = frozenset(
    ("Manuscript Image", "Image Location", "UXLC Image Location")
)

ADDRESS_REDACTION = "[address removed]"
BODY_SUFFIX = ".txt"
META_SUFFIX = ".json"

_ADDRESS_RE = re.compile(r"<?[\w.+-]+@[\w-]+(?:\.[\w-]+)+>?")
_LABEL_RE = re.compile(r"^\*?\s*(?P<label>[A-Za-z][A-Za-z /]*?):\s*(?P<value>.*)$")
_HEADING_RE = re.compile(
    r"^(?:\d+\.\s*)?"
    r"(?P<book>.+?)\s+(?P<chapter>\d+):(?P<verse>\d+)"
    r"(?:\.(?P<atom>\d+))?"
    r"(?:\s*\(Word\s+(?P<atom_paren>\d+)\))?$"
)
_FIRST_FIELD_REF_RE = re.compile(
    r"^(?P<book>.+?)\s+(?P<chapter>\d+):(?P<verse>\d+)\.(?P<atom>\d+)\s+UXLC\b"
)
# Holman names an attachment after the case it belongs to, with any remainder
# serving as its caption: "Josh 20.4.12 Daat Miqra.png".
_ATTACHMENT_REF_RE = re.compile(
    r"^(?P<book>(?:[12]\s?)?[A-Za-z]+)\s+"
    r"(?P<chapter>\d+)\.(?P<verse>\d+)\.(?P<atom>\d+)"
    r"(?P<caption>.*)$"
)
# One word in the Leviticus message, מַה־נֹּאכַל of Lev 25:20, carries the UXLC's
# note letter 'c' inside it, wrapped in the bidi controls Holman's mail client
# used to keep the Latin letter upright in a right-to-left word: LEFT-TO-RIGHT
# EMBEDDING, the letter, POP DIRECTIONAL FORMATTING, RIGHT-TO-LEFT MARK. The
# letter is the note's name, not part of the word, and it renders as a stray
# Latin letter mid-word, so it comes out along with the controls that carry it.
# Written as a named escape rather than a raw literal, which for an invisible
# character would be unreadable in the source and undiffable.
#
# The opener matched is any of the seven that start a directional run, not only
# the embedding this one message happens to use: another mail client wrapping
# the same single Latin letter in an isolate or an override is the same thing,
# and a shape that is genuinely different -- a control with no lone letter
# inside it -- still reaches the check below and raises.
_DIRECTIONAL_RUN_OPENERS = (
    "\N{LEFT-TO-RIGHT EMBEDDING}\N{RIGHT-TO-LEFT EMBEDDING}"
    "\N{LEFT-TO-RIGHT OVERRIDE}\N{RIGHT-TO-LEFT OVERRIDE}"
    "\N{LEFT-TO-RIGHT ISOLATE}\N{RIGHT-TO-LEFT ISOLATE}\N{FIRST STRONG ISOLATE}"
)
_DIRECTIONAL_RUN_CLOSERS = "\N{POP DIRECTIONAL FORMATTING}\N{POP DIRECTIONAL ISOLATE}"
_DIRECTION_MARKS = "\N{LEFT-TO-RIGHT MARK}\N{RIGHT-TO-LEFT MARK}"
_EMBEDDED_NOTE_LETTER_RE = re.compile(
    f"[{_DIRECTIONAL_RUN_OPENERS}]"
    r"\s*[A-Za-z]\s*"
    f"[{_DIRECTIONAL_RUN_CLOSERS}]"
    f"[{_DIRECTION_MARKS}]?"
)
# Every bidi formatting control, checked for after the removal above so that a
# future message embedding something in a shape this module does not know about
# raises rather than reaching the page as an invisible character.
_BIDI_CONTROL_RE = re.compile(
    f"[{_DIRECTIONAL_RUN_OPENERS}{_DIRECTIONAL_RUN_CLOSERS}{_DIRECTION_MARKS}]"
)
_NON_SLUG_RE = re.compile(r"[^a-z0-9]+")
_NORMALIZED_BOOK_TEXT_RE = re.compile(r"[^a-z0-9]")
_BK39ID_BY_NORMALIZED = {
    _NORMALIZED_BOOK_TEXT_RE.sub("", bk39id.lower()): bk39id
    for bk39id in tbn.ALL_BK39_IDS
}
# Tsefaniah is the one bk39 id that transliterates rather than anglicizes, so
# no prefix relates it to the "Zephaniah" Holman would write. This entry also
# reaches "Zeph" and "Zep" through the prefix branch of _bk39id.
_BK39ID_BY_NORMALIZED["zephaniah"] = tbn.BK_TSEF


def book_slug(book: str) -> str:
    """A bk39 id reduced to characters safe in an HTML id and a CSS class.

    "Song of Songs" is the one id with a space in it, which would otherwise
    split a whitespace-separated filter-id attribute and break a class selector.
    """
    return _NORMALIZED_BOOK_TEXT_RE.sub("", book.lower())


@dataclass(frozen=True)
class CaseRef:
    """An atom-level reference: book (a bk39 id), chapter, verse, atom index."""

    book: str
    chapter: int
    verse: int
    atom: int

    @property
    def key(self) -> str:
        """The stable key a commentary entry is filed under, e.g. Levit 7:25.6."""
        return f"{self.book} {self.chapter}:{self.verse}.{self.atom}"

    @property
    def sort_key(self) -> tuple[int, int, int, int]:
        return (tbn.get_bknu(self.book), self.chapter, self.verse, self.atom)


@dataclass(frozen=True)
class CaseImage:
    """One PNG Holman attached, assigned to the case its filename names.

    ``caption`` is what both the page and the JSON extract show, so it is
    settled here rather than in either of them: the remainder of the
    attachment's filename after the case reference, or the whole stem when the
    filename adds nothing to the reference or names no case at all.

    ``names_case_only`` marks that last-but-one kind -- a filename that is just
    the case reference, which is Holman's plain crop of the word. It orders
    first on the card, ahead of the companions he captions.
    """

    source_filename: str
    caption: str
    file_name: str
    names_case_only: bool


@dataclass(frozen=True)
class CorrectionCase:
    email_key: str
    index_in_email: int
    heading: str
    ref: CaseRef
    fields: tuple[tuple[str, str], ...]
    images: tuple[CaseImage, ...]

    @property
    def image_location(self) -> str | None:
        for label, value in self.fields:
            if label in IMAGE_LOCATION_LABELS:
                return value
        return None


@dataclass(frozen=True)
class SourceEmail:
    """One message, carrying no address.

    This repo is public, so nothing derived from a message here may hold a
    correspondent's address: only the sender's display name survives, the
    recipients are named in the page's prose rather than scraped from the To
    header, and every address in the body is replaced before the body is
    written out. Addresses live only in the .eml files, which is why those are
    kept outside the repo.
    """

    key: str
    source_file_name: str
    subject: str
    sender_name: str
    date_utc: datetime
    date_iso: str
    date_display: str
    preamble: tuple[str, ...]
    closing: tuple[str, ...]


def redact_addresses(text: str) -> str:
    """Replace every email address with a marker.

    Applied to a body the moment it is read, so no later stage can put an
    address on the page: one of these messages is a forward and quotes the
    original To and From lines in its body text. The replacement is visible
    rather than silent, because a reader should be able to tell that a line was
    edited.
    """
    return _ADDRESS_RE.sub(ADDRESS_REDACTION, text)


# ---------------------------------------------------------------- ingest


def ingest_eml_files(
    *, eml_dir: Path, emails_dir: Path, image_dir: Path
) -> dict[str, object]:
    """Write the tracked derivative of every .eml under eml_dir."""
    paths = sorted(eml_dir.glob("*.eml"))
    if not paths:
        raise ValueError(f"no .eml files found under {eml_dir}")

    emails_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    written_keys: dict[str, str] = {}
    written_images: dict[str, str] = {}
    body_count = 0
    image_count = 0
    for path in paths:
        with path.open("rb") as stream:
            message = email.message_from_binary_file(
                stream, policy=email.policy.default
            )
        key = _email_key(path)
        previous = written_keys.get(key)
        if previous is not None:
            raise ValueError(
                f"{path.name} and {previous} both reduce to the email key "
                f"{key!r}; rename one of them"
            )
        written_keys[key] = path.name

        # The .eml carries CRLF; .gitattributes normalizes this repo to LF, so
        # write LF rather than leave a tracked file that differs from its own
        # checkout.
        body = redact_addresses(_plain_text_body(message, path)).replace("\r\n", "\n")
        (emails_dir / f"{key}{BODY_SUFFIX}").write_text(
            body, encoding="utf-8", newline="\n"
        )
        body_count += 1

        attachments = []
        for source_filename, data in _png_attachments(message, path):
            file_name = f"{_NON_SLUG_RE.sub('_', Path(source_filename).stem.lower()).strip('_')}.png"
            owner = written_images.get(file_name)
            if owner is not None and owner != source_filename:
                raise ValueError(
                    f"{path.name}: attachments {source_filename!r} and {owner!r} "
                    f"both reduce to the image file {file_name!r}"
                )
            written_images[file_name] = source_filename
            (image_dir / file_name).write_bytes(data)
            attachments.append({"attachment": source_filename, "file": file_name})
            image_count += 1

        date_utc = _utc(email.utils.parsedate_to_datetime(message["Date"]))
        meta = {
            "source_file_name": path.name,
            "subject": str(message["Subject"]),
            "sender_name": _sender_display_name(message["From"]),
            "date_utc": date_utc.isoformat(),
            "body_file": f"{key}{BODY_SUFFIX}",
            "attachments": attachments,
        }
        (emails_dir / f"{key}{META_SUFFIX}").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    orphans = sorted(
        path.name for path in image_dir.glob("*.png") if path.name not in written_images
    )
    if orphans:
        raise ValueError(
            f"{image_dir} holds PNGs no message names: {orphans}. A renamed "
            "attachment leaves the file it was written under behind, tracked "
            "and served but referenced by nothing; delete them and rerun."
        )

    return {
        "eml_count": len(paths),
        "body_count": body_count,
        "image_count": image_count,
    }


def _sender_display_name(from_header: object) -> str:
    """The From header's display name, never its address."""
    display_name, address = email.utils.parseaddr(str(from_header))
    if not display_name or "@" in display_name:
        raise ValueError(
            f"From header has no address-free display name: {address!r}. "
            "This repo is public; supply the name rather than letting an "
            "address reach the derivative."
        )
    return display_name


def _email_key(path: Path) -> str:
    key = _NON_SLUG_RE.sub("-", path.stem.lower()).strip("-")
    if not key:
        raise ValueError(f"{path.name}: filename reduces to an empty email key")
    return key


def _plain_text_body(message: email.message.EmailMessage, path: Path) -> str:
    """The message's one text/plain part.

    Two would mean a forward carrying the original as a real message/rfc822
    attachment rather than as the inline quoted text the Samuel message uses,
    and taking the first would silently drop the other. That wants deciding
    rather than guessing, so it raises.
    """
    bodies = [
        part.get_content()
        for part in message.walk()
        if part.get_content_type() == "text/plain"
    ]
    if not bodies:
        raise ValueError(f"{path.name}: no text/plain part")
    if len(bodies) > 1:
        raise ValueError(
            f"{path.name}: {len(bodies)} text/plain parts; decide which is the "
            "message body before ingesting it"
        )
    return bodies[0]


def _png_attachments(
    message: email.message.EmailMessage, path: Path
) -> list[tuple[str, bytes]]:
    """Every attached PNG. A named attachment of another type is an error.

    Dropping it silently would hand the renderer a case with fewer images than
    the message has, one step before the code that would have complained.
    """
    attachments: list[tuple[str, bytes]] = []
    for part in message.walk():
        file_name = part.get_filename()
        content_type = part.get_content_type()
        if content_type != "image/png":
            if file_name is not None:
                raise ValueError(
                    f"{path.name}: attachment {file_name!r} is {content_type}, "
                    "not image/png"
                )
            continue
        if file_name is None:
            raise ValueError(f"{path.name}: image/png attachment without a filename")
        attachments.append((file_name, part.get_payload(decode=True)))
    return attachments


def _utc(when: datetime) -> datetime:
    """An aware UTC datetime, tolerating the naive result of a -0000 header."""
    if when.tzinfo is None:
        return when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc)


# ---------------------------------------------------------------- read back


def read_emails(
    emails_dir: Path, image_dir: Path
) -> tuple[list[SourceEmail], list[CorrectionCase]]:
    """Parse the tracked derivative, oldest message first."""
    meta_paths = sorted(emails_dir.glob(f"*{META_SUFFIX}"))
    if not meta_paths:
        raise ValueError(
            f"no {META_SUFFIX} files under {emails_dir}; run the ingest step first"
        )

    parsed = [_read_one(meta_path, emails_dir, image_dir) for meta_path in meta_paths]
    parsed.sort(key=lambda pair: pair[0].date_utc)
    emails = [source_email for source_email, _cases in parsed]
    cases = [case for _source_email, email_cases in parsed for case in email_cases]
    cases.sort(key=lambda case: case.ref.sort_key)
    _require_distinct_refs(cases)
    return emails, cases


def _read_one(
    meta_path: Path, emails_dir: Path, image_dir: Path
) -> tuple[SourceEmail, list[CorrectionCase]]:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    key = meta_path.stem
    body_path = emails_dir / meta["body_file"]
    body = body_path.read_text(encoding="utf-8")
    preamble, raw_cases, closing = _split_body_into_cases(body, body_path)
    cases = [
        _build_case(
            email_key=key,
            index_in_email=index,
            heading=heading,
            fields=fields,
            path=body_path,
        )
        for index, (heading, fields) in enumerate(raw_cases, start=1)
    ]
    attachments = [
        (entry["attachment"], entry["file"]) for entry in meta["attachments"]
    ]
    for _source_filename, file_name in attachments:
        if not (image_dir / file_name).is_file():
            raise ValueError(
                f"{meta_path.name} names the image {file_name!r}, which is not "
                f"in {image_dir}; rerun the ingest step"
            )
    cases = _assign_images(cases, attachments, meta_path)

    date_utc = datetime.fromisoformat(meta["date_utc"])
    source_email = SourceEmail(
        key=key,
        source_file_name=meta["source_file_name"],
        subject=meta["subject"],
        sender_name=meta["sender_name"],
        date_utc=date_utc,
        date_iso=date_utc.isoformat(),
        date_display=date_utc.strftime("%d %B %Y"),
        preamble=preamble,
        closing=closing,
    )
    return source_email, cases


def _labelled(line: str) -> tuple[str, str] | None:
    match = _LABEL_RE.match(line)
    if match is None:
        return None
    label = match.group("label").strip()
    if label not in KNOWN_FIELD_LABELS:
        return None
    return label, match.group("value").strip()


def _split_body_into_cases(
    body: str, path: Path
) -> tuple[
    tuple[str, ...], list[tuple[str, tuple[tuple[str, str], ...]]], tuple[str, ...]
]:
    lines = [
        _without_embedded_note_letter(line.rstrip(), path) for line in body.splitlines()
    ]
    starts = _case_start_indexes(lines)
    if not starts:
        raise ValueError(f"{path.name}: no cases found")
    _require_no_unopened_case(lines[: starts[0]], path)

    preamble = tuple(line.strip() for line in lines[: starts[0]] if line.strip())
    cases: list[tuple[str, tuple[tuple[str, str], ...]]] = []
    closing: tuple[str, ...] = ()
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        heading = lines[start].strip()
        fields, trailing = _parse_case_region(lines[start + 1 : end], heading, path)
        cases.append((heading, fields))
        if not trailing:
            continue
        if position + 1 < len(starts):
            raise ValueError(
                f"{path.name}: unexpected prose after case {heading!r}: {trailing[0]!r}"
            )
        closing = trailing
    return preamble, cases, closing


def _without_embedded_note_letter(line: str, path: Path) -> str:
    """Drop a bidi-embedded Latin note letter, and raise on any control left.

    Applied to every line of a body as it is split, so the heading, the fields,
    the greeting and the sign-off are all read from cleaned text and no later
    stage has to know about this. The tracked ``emails/<key>.txt`` still holds
    the message as it arrived; this is a reading of it, and the page says so.
    """
    cleaned = _EMBEDDED_NOTE_LETTER_RE.sub("", line)
    leftover = _BIDI_CONTROL_RE.search(cleaned)
    if leftover is not None:
        raise ValueError(
            f"{path.name}: bidi formatting control "
            f"U+{ord(leftover.group()):04X} survives in {cleaned.strip()!r}. "
            "Widen _EMBEDDED_NOTE_LETTER_RE, or decide what this one means, "
            "rather than letting an invisible character reach the page."
        )
    return cleaned


def _require_no_unopened_case(preamble_lines: list[str], path: Path) -> None:
    """Raise on a case the start scan failed to open, rather than read it as prose.

    A case opens only when the line after its heading is a label in
    FIRST_FIELD_LABELS, so a message introducing a new spelling for its FIRST
    field opens no case at all: the heading and every field line fall before
    the first case and would be shown as the message's greeting.
    ``_parse_case_region``'s unrecognized-label check cannot see them, because
    it only runs inside a case that did open.

    The rule has to be narrow, because the forwarded Samuel message quotes
    Sent/From/To/Subject lines in its real preamble. What distinguishes a
    dropped case is that its label-shaped line sits directly under a
    heading-shaped one, which is true of none of those four.
    """
    previous_nonblank: str | None = None
    for line in preamble_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if (
            _LABEL_RE.match(line) is not None
            and _labelled(line) is None
            and previous_nonblank is not None
            and _HEADING_RE.match(previous_nonblank) is not None
        ):
            raise ValueError(
                f"{path.name}: {stripped!r} under the heading "
                f"{previous_nonblank!r} looks like the first field of a case, "
                "but its label is not one of FIRST_FIELD_LABELS, so no case "
                "opened. Add the spelling to FIRST_FIELD_LABELS."
            )
        previous_nonblank = stripped


def _case_start_indexes(lines: list[str]) -> list[int]:
    starts: list[int] = []
    for index, line in enumerate(lines):
        if not line.strip() or _labelled(line) is not None:
            continue
        following = next(
            (later for later in range(index + 1, len(lines)) if lines[later].strip()),
            None,
        )
        if following is None:
            continue
        field = _labelled(lines[following])
        if field is not None and field[0] in FIRST_FIELD_LABELS:
            starts.append(index)
    return starts


def _parse_case_region(
    region: list[str], heading: str, path: Path
) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    """Split one case's lines into its labelled fields and any trailing prose.

    A field value is one line. Prose after the fields is the message's sign-off,
    and only the last case in a message may have any. An unrecognized label
    raises here rather than being absorbed into that sign-off, which is what
    would otherwise happen to a new label spelling in a future message. The
    check has to live in this function: applied to a whole body it would reject
    the forwarded Sent/From/To/Subject block one of these messages quotes in
    its preamble. It reaches only a case that opened, so the same mistake in a
    message's FIRST field is caught by ``_require_no_unopened_case`` instead.
    """
    fields: list[tuple[str, str]] = []
    trailing: list[str] = []
    after_blank = True
    for line in region:
        stripped = line.strip()
        if not stripped:
            after_blank = True
            continue
        field = _labelled(line)
        if field is not None:
            if trailing:
                raise ValueError(
                    f"{path.name}: field {field[0]!r} follows the prose "
                    f"{trailing[0]!r} in case {heading!r}"
                )
            fields.append(field)
            after_blank = False
            continue
        if _LABEL_RE.match(line) is not None:
            raise ValueError(
                f"{path.name}: unrecognized field label in case {heading!r}: "
                f"{stripped!r}. Add it to FIRST_FIELD_LABELS or OTHER_FIELD_LABELS."
            )
        if not after_blank and not trailing:
            raise ValueError(
                f"{path.name}: unlabelled line inside case {heading!r}: {stripped!r}"
            )
        trailing.append(stripped)
    if not fields:
        raise ValueError(f"{path.name}: case {heading!r} has no labelled fields")
    return tuple(fields), tuple(trailing)


def _build_case(
    *,
    email_key: str,
    index_in_email: int,
    heading: str,
    fields: tuple[tuple[str, str], ...],
    path: Path,
) -> CorrectionCase:
    match = _HEADING_RE.match(heading)
    if match is None:
        raise ValueError(f"{path.name}: unparsable case heading {heading!r}")
    book = _bk39id(match.group("book"), path)
    chapter = int(match.group("chapter"))
    verse = int(match.group("verse"))
    atom_text = match.group("atom") or match.group("atom_paren")

    field_ref = _ref_from_first_field(fields[0][1], path)
    if field_ref is not None:
        if (field_ref.book, field_ref.chapter, field_ref.verse) != (
            book,
            chapter,
            verse,
        ):
            raise ValueError(
                f"{path.name}: heading {heading!r} disagrees with its "
                f"{fields[0][0]} field {fields[0][1]!r}"
            )
        if atom_text is not None and int(atom_text) != field_ref.atom:
            raise ValueError(
                f"{path.name}: heading {heading!r} atom index disagrees with "
                f"its {fields[0][0]} field"
            )
        atom_text = str(field_ref.atom)

    if atom_text is None:
        raise ValueError(f"{path.name}: case {heading!r} names no atom index")

    return CorrectionCase(
        email_key=email_key,
        index_in_email=index_in_email,
        heading=heading,
        ref=CaseRef(book=book, chapter=chapter, verse=verse, atom=int(atom_text)),
        fields=fields,
        images=(),
    )


def _ref_from_first_field(value: str, path: Path) -> CaseRef | None:
    match = _FIRST_FIELD_REF_RE.match(value)
    if match is None:
        return None
    return CaseRef(
        book=_bk39id(match.group("book"), path),
        chapter=int(match.group("chapter")),
        verse=int(match.group("verse")),
        atom=int(match.group("atom")),
    )


def _bk39id(book_text: str, path: Path) -> str:
    """Resolve Holman's book spelling to a bk39 id, by exact or unique prefix.

    Matching runs both ways because it has to. Holman's abbreviations are
    prefixes of the id -- Ex, Lev, Josh, Judg, 1Sa, "2 Samuel" -- but two bk39
    ids are themselves truncations, so his "Deuteronomy" and "Leviticus" have
    the id (Deuter, Levit) as their prefix instead. Either direction resolving
    to exactly one book is a match; anything else raises, rather than guessing.
    """
    wanted = _NORMALIZED_BOOK_TEXT_RE.sub("", book_text.lower())
    exact = _BK39ID_BY_NORMALIZED.get(wanted)
    if exact is not None:
        return exact
    matched = sorted(
        set(
            bk39id
            for normalized, bk39id in _BK39ID_BY_NORMALIZED.items()
            if normalized.startswith(wanted) or wanted.startswith(normalized)
        )
    )
    if len(matched) == 1:
        return matched[0]
    if not matched:
        raise ValueError(f"{path.name}: unrecognized book name {book_text!r}")
    raise ValueError(
        f"{path.name}: ambiguous book name {book_text!r} (matches {matched})"
    )


def _assign_images(
    cases: list[CorrectionCase],
    attachments: list[tuple[str, str]],
    path: Path,
) -> list[CorrectionCase]:
    """Attach each PNG to the case its filename names.

    A filename such as "Josh 20.4.12 Daat Miqra.png" names its case outright and
    its remainder becomes the caption. A filename naming no case (Holman's
    "Sassoon 1053.png") belongs to a single-case message; in a multi-case
    message it is an error rather than a guess.
    """
    by_ref: dict[str, list[CaseImage]] = {case.ref.key: [] for case in cases}
    unreferenced: list[CaseImage] = []
    for source_filename, file_name in attachments:
        stem = Path(source_filename).stem
        match = _ATTACHMENT_REF_RE.match(stem)
        if match is None:
            unreferenced.append(
                CaseImage(
                    source_filename=source_filename,
                    caption=stem.strip(),
                    file_name=file_name,
                    names_case_only=False,
                )
            )
            continue
        ref = CaseRef(
            book=_bk39id(match.group("book"), path),
            chapter=int(match.group("chapter")),
            verse=int(match.group("verse")),
            atom=int(match.group("atom")),
        )
        if ref.key not in by_ref:
            raise ValueError(
                f"{path.name}: attachment {source_filename!r} names {ref.key}, "
                "which is not a case in this message"
            )
        # Holman's "2Sa 5.21.1 .png" has a space before the extension, so the
        # stem needs stripping too, not only the remainder after the reference.
        remainder = match.group("caption").strip()
        by_ref[ref.key].append(
            CaseImage(
                source_filename=source_filename,
                caption=remainder or stem.strip(),
                file_name=file_name,
                names_case_only=not remainder,
            )
        )
    if unreferenced:
        if len(cases) != 1:
            raise ValueError(
                f"{path.name}: attachments "
                f"{[image.source_filename for image in unreferenced]} name no "
                f"case, and this message has {len(cases)} cases"
            )
        by_ref[cases[0].ref.key].extend(unreferenced)

    return [
        CorrectionCase(
            email_key=case.email_key,
            index_in_email=case.index_in_email,
            heading=case.heading,
            ref=case.ref,
            fields=case.fields,
            images=tuple(_ordered_images(by_ref[case.ref.key])),
        )
        for case in cases
    ]


def _ordered_images(images: list[CaseImage]) -> list[CaseImage]:
    """The plain crop of the word first, then Holman's companions by caption."""
    return sorted(images, key=lambda image: (not image.names_case_only, image.caption))


def _require_distinct_refs(cases: list[CorrectionCase]) -> None:
    seen: dict[str, CorrectionCase] = {}
    for case in cases:
        previous = seen.get(case.ref.key)
        if previous is not None:
            where = (
                f"both in {case.email_key}"
                if previous.email_key == case.email_key
                else f"in {previous.email_key} and {case.email_key}"
            )
            raise ValueError(
                f"two cases share the reference {case.ref.key}: "
                f"case {previous.index_in_email} {previous.heading!r} and "
                f"case {case.index_in_email} {case.heading!r}, {where}"
            )
        seen[case.ref.key] = case
