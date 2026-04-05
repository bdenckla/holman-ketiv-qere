from __future__ import annotations

import json
from pathlib import Path

from pycmn import bib_locales
from python_modules.hebrew_text_tokens import (
    find_hebrew_tokens,
    strip_ignorable_token_marks,
)
from python_modules.mam_plus_verse_data import verse_texts_by_location


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUS_DIR = (REPO_ROOT.parent / "mam-parsed" / "plus").resolve()
TARGET_VERSE = ("Tsefaniah", 2, 9)


def book_names_for_plus_file(path: Path, plus_json: dict[str, object]) -> list[str]:
    book39s = plus_json.get("book39s")
    if not isinstance(book39s, list):
        raise ValueError("plus JSON missing list key 'book39s'")

    bk24id = path.stem.split("-", 1)[1]
    names = list(bib_locales.bk39ids_of_bk24(bk24id))
    if len(names) != len(book39s):
        raise ValueError(
            f"book-name mismatch for {path.name}: expected {len(book39s)} names, got {len(names)}"
        )
    return names


def strip_ignorable_marks(token: str) -> str:
    return strip_ignorable_token_marks(token)


def is_final_hiriq_token(token: str) -> bool:
    return strip_ignorable_marks(token).endswith("\u05B4")


def find_final_hiriq_hits() -> tuple[list[dict[str, object]], list[str]]:
    hits: list[dict[str, object]] = []
    target_tokens: list[str] = []

    for path in sorted(PLUS_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            plus_json = json.load(handle)

        verse_texts = verse_texts_by_location(plus_json)
        book_names = book_names_for_plus_file(path, plus_json)

        for (book39_index, chapter_num, verse_num), verse_text in verse_texts.items():
            book_name = book_names[book39_index]
            tokens = find_hebrew_tokens(verse_text)

            if (book_name, chapter_num, verse_num) == TARGET_VERSE:
                target_tokens = tokens

            for token in tokens:
                if not is_final_hiriq_token(token):
                    continue

                hits.append(
                    {
                        "book": book_name,
                        "chapter": chapter_num,
                        "verse": verse_num,
                        "token": token,
                        "deaccented": strip_ignorable_marks(token),
                        "file": path.name,
                    }
                )

    return hits, target_tokens


def main() -> None:
    hits, target_tokens = find_final_hiriq_hits()

    print(f"total_hits={len(hits)}")
    for hit in hits:
        print(
            f"{hit['book']} {hit['chapter']}:{hit['verse']}\t"
            f"{hit['token']}\tdeaccented={hit['deaccented']}\tfile={hit['file']}"
        )

    print("target_verse_tokens=")
    print(" ".join(target_tokens))

    print("target_verse_final_hiriq_tokens=")
    print(" ".join(token for token in target_tokens if is_final_hiriq_token(token)))


if __name__ == "__main__":
    main()