from __future__ import annotations

import re


HEBREW_TOKEN_CHAR_CLASS = (
    "\u034F"
    "\u0591-\u05BD"
    "\u05BF"
    "\u05C1-\u05C2"
    "\u05C4-\u05C5"
    "\u05C7"
    "\u05D0-\u05EA"
    "\u05F0-\u05F2"
    "\u200C-\u200D"
    "\uFB1D-\uFB4F"
)
HEBREW_TOKEN_PATTERN = re.compile(f"[{HEBREW_TOKEN_CHAR_CLASS}]+")
IGNORABLE_ACCENTS_METEG_AND_JOINERS_RE = re.compile(
    "["
    "\u034F"
    "\u0591-\u05AF"
    "\u05BD"
    "\u200C-\u200D"
    "]+"
)


def find_hebrew_tokens(text: str) -> list[str]:
    return HEBREW_TOKEN_PATTERN.findall(text)


def strip_ignorable_token_marks(text: str) -> str:
    return IGNORABLE_ACCENTS_METEG_AND_JOINERS_RE.sub("", text)