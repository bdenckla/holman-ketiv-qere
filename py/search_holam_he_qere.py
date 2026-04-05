from __future__ import annotations

"""Search MPP qere readings for holam-he word endings.

This tracked script serves two purposes:

1. Reproduce the current holam-he qere search.
2. Provide a concrete template for future phenomenon searches that compare
   direct MPP traversal against the MAM-basics qere-word list.

The script treats MPP as the source of truth and uses the MAM-basics word
list as a sanity check. It also records which MPP hits came from the first
argument of קו"כ-אם.
"""

import json
import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAM_PARSED_PLUS_DIR = REPO_ROOT.parent / "MAM-parsed" / "plus"
MAM_BASICS_QERE_WORDS_PATH = (
    REPO_ROOT.parent / "MAM-basics" / "out" / "mam-qere-words.json"
)
OUTPUT_PATH = REPO_ROOT / ".novc" / "holam_he_qere_report.json"

ACCENTS_AND_METEG_RE = re.compile(r"[\u0591-\u05AF\u05BD\u05BF\u05C0\u05C4\u05C5]")
CGJ_AND_JOINERS_RE = re.compile(r"[\u034F\u200C\u200D]")
TOKEN_SEPARATOR_CHARS = {" ", "\n", "\r", "\t", "\u05BE", "\u05C0", "\u05C3"}
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


def is_holam_he_word(word: str) -> bool:
    vowel_only = to_vowel_only_form(word)
    return vowel_only.endswith("\u05B9\u05D4")


def he_to_int_map(plus_json: dict[str, object]) -> dict[str, int]:
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


def with_source(
    source: dict[str, object] | None,
    template_name: str,
    argument_key: str,
) -> dict[str, object]:
    return {
        "template_name": template_name,
        "argument_key": argument_key,
        "is_qoq_if_arg1": template_name == 'קו"כ-אם' and argument_key == "1",
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
            source=with_source(source, tmpl_name, qere_arg_key),
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


def extract_qere_segments(
    node: object,
    *,
    source: dict[str, object] | None,
) -> list[dict[str, object]]:
    if isinstance(node, str):
        return [{"text": node, "source": source}]

    if isinstance(node, list):
        out: list[dict[str, object]] = []
        for item in node:
            out.extend(extract_qere_segments(item, source=source))
        return out

    if not isinstance(node, dict):
        return []

    tmpl_name = node.get("tmpl_name")
    tmpl_params = node.get("tmpl_params")
    if not isinstance(tmpl_name, str) or not isinstance(tmpl_params, dict):
        return []

    if tmpl_name == "נוסח":
        return extract_qere_segments(tmpl_params.get("1"), source=source)

    if tmpl_name == 'מ:הערה-2':
        return extract_qere_segments(tmpl_params.get("1"), source=source)

    if tmpl_name == "מ:הערה":
        return []

    qere_arg_key = qere_arg_key_for_template(tmpl_name)
    if qere_arg_key is not None:
        return extract_qere_segments(
            tmpl_params.get(qere_arg_key),
            source=with_source(source, tmpl_name, qere_arg_key),
        )

    if tmpl_name in WHITESPACE_TEMPLATE_NAMES:
        return [{"text": " ", "source": source}]

    if tmpl_name in {"כתיב ולא קרי", 'מ:נו"ן הפוכה'}:
        return []

    if tmpl_name in {"מ:פסק", "מ:לגרמיה-2"}:
        return [{"text": "\u05C0", "source": source}]

    if tmpl_name == "מ:מקף אפור":
        return [{"text": "\u05BE", "source": source}]

    out: list[dict[str, object]] = []
    for value in tmpl_params.values():
        out.extend(extract_qere_segments(value, source=source))
    return out


def flatten_sources(source: dict[str, object] | None) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    current = source
    while isinstance(current, dict):
        out.append(
            {
                "template_name": current.get("template_name"),
                "argument_key": current.get("argument_key"),
                "is_qoq_if_arg1": bool(current.get("is_qoq_if_arg1")),
            }
        )
        current = current.get("parent_source")
    return out


def iter_tokens_from_segments(segments: list[dict[str, object]]) -> list[dict[str, object]]:
    tokens: list[dict[str, object]] = []
    current_chars: list[str] = []
    current_sources: list[dict[str, object] | None] = []

    def flush() -> None:
        if not current_chars:
            return

        flattened: list[dict[str, object]] = []
        for source in current_sources:
            flattened.extend(flatten_sources(source))

        seen: set[tuple[object, object, object]] = set()
        unique_sources: list[dict[str, object]] = []
        for item in flattened:
            marker = (
                item.get("template_name"),
                item.get("argument_key"),
                item.get("is_qoq_if_arg1"),
            )
            if marker in seen:
                continue
            seen.add(marker)
            unique_sources.append(item)

        tokens.append({"word": "".join(current_chars), "sources": unique_sources})
        current_chars.clear()
        current_sources.clear()

    for segment in segments:
        text = segment.get("text")
        source = segment.get("source")
        if not isinstance(text, str):
            continue
        for char in text:
            if char in TOKEN_SEPARATOR_CHARS:
                flush()
                continue
            current_chars.append(char)
            current_sources.append(source if isinstance(source, dict) else None)

    flush()
    return tokens


def iter_plus_verses(plus_json: dict[str, object], plus_file_name: str):
    mapping = he_to_int_map(plus_json)
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


def load_mpp_hits() -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []

    for plus_path in sorted(MAM_PARSED_PLUS_DIR.glob("*.json")):
        with open(plus_path, encoding="utf-8") as handle:
            plus_json = json.load(handle)

        for verse_info in iter_plus_verses(plus_json, plus_path.name):
            qere_atoms = project_qere_atoms(verse_info["ep_payload"], source=None)
            tokens = word_atoms_from_qere_atoms(qere_atoms)

            for token in tokens:
                word = token["word"]
                if not isinstance(word, str) or not is_holam_he_word(word):
                    continue

                sources = token["sources"]
                if not isinstance(sources, list):
                    sources = []

                source_templates = sorted(
                    {
                        item["template_name"]
                        for item in sources
                        if isinstance(item.get("template_name"), str)
                    }
                )
                source_argument_keys = sorted(
                    {
                        item["argument_key"]
                        for item in sources
                        if isinstance(item.get("argument_key"), str)
                    }
                )
                is_qoq_if_arg1 = any(
                    bool(item.get("is_qoq_if_arg1"))
                    for item in sources
                    if isinstance(item, dict)
                )

                hits.append(
                    {
                        "plus_file": verse_info["plus_file"],
                        "book39_index": verse_info["book39_index"],
                        "book24_name": verse_info["book24_name"],
                        "sub_book_name": verse_info["sub_book_name"],
                        "chapter": verse_info["chapter"],
                        "verse": verse_info["verse"],
                        "word": word,
                        "vowel_only_form": to_vowel_only_form(word),
                        "is_qoq_if_arg1": is_qoq_if_arg1,
                        "source_templates": source_templates,
                        "source_argument_keys": source_argument_keys,
                        "is_plain_text_hit": len(source_templates) == 0,
                    }
                )

    return hits


def load_wordlist_hits() -> list[dict[str, str]]:
    with open(MAM_BASICS_QERE_WORDS_PATH, encoding="utf-8") as handle:
        words = json.load(handle)
    if not isinstance(words, list):
        raise ValueError("mam-qere-words.json must be a list")

    hits: list[dict[str, str]] = []
    for word in words:
        if isinstance(word, str) and is_holam_he_word(word):
            hits.append(
                {
                    "word": word,
                    "vowel_only_form": to_vowel_only_form(word),
                }
            )
    return hits


def summarize_mpp_hits(hits: list[dict[str, object]]) -> dict[str, object]:
    vowel_only_counter = Counter(hit["vowel_only_form"] for hit in hits)
    qoq_if_hits = [hit for hit in hits if hit["is_qoq_if_arg1"]]
    other_hits = [hit for hit in hits if not hit["is_qoq_if_arg1"]]
    plain_hits = [hit for hit in hits if hit["is_plain_text_hit"]]
    templated_non_qoq_if_hits = [
        hit for hit in hits if not hit["is_qoq_if_arg1"] and not hit["is_plain_text_hit"]
    ]

    return {
        "hit_count": len(hits),
        "unique_vowel_only_form_count": len(vowel_only_counter),
        "qoq_if_arg1_hit_count": len(qoq_if_hits),
        "qoq_if_arg1_unique_vowel_only_form_count": len(
            {hit["vowel_only_form"] for hit in qoq_if_hits}
        ),
        "other_hit_count": len(other_hits),
        "other_unique_vowel_only_form_count": len(
            {hit["vowel_only_form"] for hit in other_hits}
        ),
        "plain_text_hit_count": len(plain_hits),
        "templated_non_qoq_if_hit_count": len(templated_non_qoq_if_hits),
        "source_template_hit_counts": dict(
            sorted(
                Counter(
                    template_name
                    for hit in hits
                    for template_name in hit["source_templates"]
                ).items()
            )
        ),
        "vowel_only_form_counts": dict(sorted(vowel_only_counter.items())),
    }


def hit_source_category(hit: dict[str, object]) -> str:
    if hit["is_qoq_if_arg1"]:
        return "qoq_if_arg1"
    if hit["is_plain_text_hit"]:
        return "plain_text"
    return "templated_other"


def verse_indexed_hits(hits: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], dict[str, object]] = {}

    for hit in hits:
        key = (
            hit["plus_file"],
            hit["book39_index"],
            hit["chapter"],
            hit["verse"],
            hit["book24_name"],
            hit["sub_book_name"],
        )
        if key not in grouped:
            grouped[key] = {
                "plus_file": hit["plus_file"],
                "book39_index": hit["book39_index"],
                "book24_name": hit["book24_name"],
                "sub_book_name": hit["sub_book_name"],
                "chapter": hit["chapter"],
                "verse": hit["verse"],
                "hits": [],
            }

        grouped[key]["hits"].append(
            {
                "word": hit["word"],
                "vowel_only_form": hit["vowel_only_form"],
                "source_category": hit_source_category(hit),
                "source_templates": hit["source_templates"],
                "source_argument_keys": hit["source_argument_keys"],
            }
        )

    out = list(grouped.values())
    out.sort(
        key=lambda item: (
            str(item["plus_file"]),
            int(item["book39_index"]),
            int(item["chapter"]),
            int(item["verse"]),
        )
    )
    return out


def build_report() -> dict[str, object]:
    mpp_hits = load_mpp_hits()
    wordlist_hits = load_wordlist_hits()

    mpp_vowel_only_forms = {hit["vowel_only_form"] for hit in mpp_hits}
    wordlist_vowel_only_forms = {hit["vowel_only_form"] for hit in wordlist_hits}

    return {
        "summary": {
            "mpp": summarize_mpp_hits(mpp_hits),
            "mam_basics_wordlist_hit_count": len(wordlist_hits),
            "mam_basics_wordlist_unique_vowel_only_form_count": len(wordlist_vowel_only_forms),
            "vowel_only_forms_only_in_mpp": sorted(mpp_vowel_only_forms - wordlist_vowel_only_forms),
            "vowel_only_forms_only_in_wordlist": sorted(wordlist_vowel_only_forms - mpp_vowel_only_forms),
            "vowel_only_forms_in_both": sorted(mpp_vowel_only_forms & wordlist_vowel_only_forms),
        },
        "mpp_hits_qoq_if_arg1": [hit for hit in mpp_hits if hit["is_qoq_if_arg1"]],
        "mpp_hits_other": [hit for hit in mpp_hits if not hit["is_qoq_if_arg1"]],
        "mpp_hits_plain_text": [hit for hit in mpp_hits if hit["is_plain_text_hit"]],
        "mpp_hits_by_verse": verse_indexed_hits(mpp_hits),
        "mpp_templated_hits_by_verse": verse_indexed_hits(
            [hit for hit in mpp_hits if not hit["is_plain_text_hit"]]
        ),
        "mam_basics_wordlist_hits": wordlist_hits,
    }


def main() -> None:
    report = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(str(OUTPUT_PATH))
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()