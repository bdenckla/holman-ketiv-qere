from __future__ import annotations

from collections.abc import Iterator
import re


ACCENTS_AND_METEG_RE = re.compile(r"[\u0591-\u05AF\u05BD\u05BF\u05C0\u05C4\u05C5]")
CGJ_AND_JOINERS_RE = re.compile(r"[\u034F\u200C\u200D]")
TOKEN_SPLIT_RE = re.compile(r"[\s\u05BE\u05C0\u05C3]+")
WHITESPACE_TEMPLATE_NAMES = {
    "מ:ששש",
    "סס",
    "פפ",
    "ססס",
    "פפפ",
    "ר0",
    "ר1",
    "ר2",
    "ר3",
}
IN_WORD_RECURSE_TEMPLATE_NAMES = {
    "מ:אות-ג",
    "מ:אות-ק",
    "מ:אות תלויה",
    "מ:אות-מיוחדת-במילה",
}
PARAM_BOUNDARY_TEMPLATE_NAMES = {
    "מ:דחי",
    "מ:צינור",
    "מ:קמץ",
    "מ:כפול",
}


def to_vowel_only_form(text: str) -> str:
    no_joiners = CGJ_AND_JOINERS_RE.sub("", text)
    return ACCENTS_AND_METEG_RE.sub("", no_joiners)


def strip_accents_and_meteg(text: str) -> str:
    """Backward-compatible alias for scratch helpers."""
    return to_vowel_only_form(text)


def qere_arg_key_for_template(template_name: str) -> str | None:
    if template_name == 'קו"כ-אם':
        return "1"
    if template_name == "קרי ולא כתיב":
        return "2"
    if template_name == "כתיב ולא קרי":
        return None
    if "כו\"ק" in template_name or "קו\"כ" in template_name:
        return "2"
    return None


def _with_source(
    source: dict[str, object] | None,
    template_name: str,
    argument_key: str,
) -> dict[str, object]:
    return {
        "template_name": template_name,
        "argument_key": argument_key,
        "is_trivq_arg1": template_name == 'קו"כ-אם' and argument_key == "1",
        "parent_source": source,
    }


def _text_atom(text: str, source: dict[str, object] | None) -> dict[str, object]:
    return {
        "kind": "text",
        "text": text,
        "source": source,
    }


def _template_atom(
    template_name: str,
    param_atom_lists: list[list[dict[str, object]]],
) -> dict[str, object]:
    return {
        "kind": "template",
        "template_name": template_name,
        "param_atom_lists": param_atom_lists,
    }


def project_qere_atoms(
    node: object,
    *,
    source: dict[str, object] | None,
) -> list[dict[str, object]]:
    if isinstance(node, str):
        return [_text_atom(node, source)]

    if isinstance(node, list):
        out: list[dict[str, object]] = []
        for item in node:
            out.extend(project_qere_atoms(item, source=source))
        return out

    if not isinstance(node, dict):
        return []

    tmpl_name = node.get("tmpl_name")
    tmpl_params = node.get("tmpl_params")
    if not isinstance(tmpl_name, str) or not isinstance(tmpl_params, dict):
        return []

    if tmpl_name in {"נוסח", 'מ:הערה-2'}:
        return project_qere_atoms(tmpl_params.get("1"), source=source)

    if tmpl_name in {"מ:הערה", "כתיב ולא קרי", 'מ:נו"ן הפוכה'}:
        return []

    qere_arg_key = qere_arg_key_for_template(tmpl_name)
    if qere_arg_key is not None:
        return project_qere_atoms(
            tmpl_params.get(qere_arg_key),
            source=_with_source(source, tmpl_name, qere_arg_key),
        )

    if tmpl_name in WHITESPACE_TEMPLATE_NAMES:
        return [_text_atom(" ", source)]

    if tmpl_name in {"מ:פסק", "מ:לגרמיה-2"}:
        return [_text_atom("\u05C0", source)]

    if tmpl_name == "מ:מקף אפור":
        return [_text_atom("\u05BE", source)]

    if tmpl_name in IN_WORD_RECURSE_TEMPLATE_NAMES:
        return project_qere_atoms(tmpl_params.get("1"), source=source)

    if tmpl_name in PARAM_BOUNDARY_TEMPLATE_NAMES:
        return [
            _template_atom(
                tmpl_name,
                [
                    project_qere_atoms(value, source=source)
                    for value in tmpl_params.values()
                ],
            )
        ]

    out: list[dict[str, object]] = []
    for value in tmpl_params.values():
        out.extend(project_qere_atoms(value, source=source))
    return out


def flatten_sources(source: dict[str, object] | None) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    current = source
    while isinstance(current, dict):
        out.append(
            {
                "template_name": current.get("template_name"),
                "argument_key": current.get("argument_key"),
                "is_trivq_arg1": bool(current.get("is_trivq_arg1")),
            }
        )
        current = current.get("parent_source")
    return out


def _word_atoms_from_text_atom(atom: dict[str, object]) -> list[dict[str, object]]:
    text = atom.get("text")
    if not isinstance(text, str):
        return []

    source = atom.get("source")
    sources = flatten_sources(source if isinstance(source, dict) else None)
    return [
        {
            "word": part,
            "sources": list(sources),
        }
        for part in TOKEN_SPLIT_RE.split(text)
        if part
    ]


def word_atoms_from_qere_atoms(atoms: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for atom in atoms:
        kind = atom.get("kind")
        if kind == "text":
            out.extend(_word_atoms_from_text_atom(atom))
            continue
        if kind == "template":
            param_atom_lists = atom.get("param_atom_lists")
            if not isinstance(param_atom_lists, list):
                continue
            for param_atoms in param_atom_lists:
                if not isinstance(param_atoms, list):
                    continue
                out.extend(word_atoms_from_qere_atoms(param_atoms))
    return out


def _he_to_int_map(plus_json: dict[str, object]) -> dict[str, int]:
    header = plus_json.get("header")
    if not isinstance(header, dict):
        raise ValueError("plus JSON missing header")
    mapping = header.get("he_to_int")
    if not isinstance(mapping, dict):
        raise ValueError("plus JSON header missing he_to_int")

    out: dict[str, int] = {}
    for key, value in mapping.items():
        if isinstance(key, str) and isinstance(value, int):
            out[key] = value
    return out


def iter_plus_verses(
    plus_json: dict[str, object],
    plus_file_name: str,
) -> Iterator[dict[str, object]]:
    mapping = _he_to_int_map(plus_json)
    book39s = plus_json.get("book39s")
    if not isinstance(book39s, list):
        raise ValueError("plus JSON missing book39s")

    for book39_index, book39 in enumerate(book39s):
        if not isinstance(book39, dict):
            continue
        book_name = book39.get("book24_name")
        sub_book_name = book39.get("sub_book_name")
        chapters = book39.get("chapters")
        if not isinstance(chapters, dict):
            continue

        for he_chapter, verses in chapters.items():
            if he_chapter in ("0", "תתת"):
                continue
            chapter_num = mapping.get(he_chapter)
            if not isinstance(chapter_num, int) or not isinstance(verses, dict):
                continue

            for he_verse, verse_payload in verses.items():
                if he_verse in ("0", "תתת"):
                    continue
                verse_num = mapping.get(he_verse)
                if not isinstance(verse_num, int):
                    continue
                if not isinstance(verse_payload, list) or len(verse_payload) < 3:
                    continue

                yield {
                    "plus_file": plus_file_name,
                    "book39_index": book39_index,
                    "book24_name": book_name,
                    "sub_book_name": sub_book_name,
                    "chapter": chapter_num,
                    "verse": verse_num,
                    "ep_payload": verse_payload[2],
                }