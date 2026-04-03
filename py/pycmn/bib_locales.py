"""
Vendored subset of MAM-basics/py/pycmn/bib_locales.py.

This file keeps the standard 39-book names and MAM short abbreviations
needed by the local extractor without taking a runtime dependency on the
neighboring MAM-basics repository.
"""


def short(bk39id: str) -> str:
    """Return the MAM short book abbreviation for a standard 39-book name."""
    return _SHORT_BY_STD[bk39id]


def std_from_short(short_book_name: str) -> str:
    """Return the standard 39-book name for a MAM short book abbreviation."""
    return _STD_BY_SHORT[short_book_name]


BK_JOSHUA = "Joshua"
BK_JUDGES = "Judges"
BK_FST_SAM = "1Samuel"
BK_SND_SAM = "2Samuel"
BK_FST_KGS = "1Kings"
BK_SND_KGS = "2Kings"
BK_ISAIAH = "Isaiah"
BK_JEREM = "Jeremiah"
BK_EZEKIEL = "Ezekiel"
BK_PSALMS = "Psalms"
BK_PROV = "Proverbs"
BK_JOB = "Job"
BK_TSEF = "Tsefaniah"
BK_FST_CHR = "1Chronicles"
BK_SND_CHR = "2Chronicles"

_SHORT_BY_STD = {
    BK_JOSHUA: "Js",
    BK_JUDGES: "Ju",
    BK_FST_SAM: "1S",
    BK_SND_SAM: "2S",
    BK_FST_KGS: "1K",
    BK_SND_KGS: "2K",
    BK_ISAIAH: "I",
    BK_JEREM: "Je",
    BK_EZEKIEL: "Ee",
    BK_PSALMS: "Ps",
    BK_PROV: "Pr",
    BK_JOB: "Jb",
    BK_TSEF: "Ts",
    BK_FST_CHR: "1C",
    BK_SND_CHR: "2C",
}

_STD_BY_SHORT = {short_name: std_name for std_name, short_name in _SHORT_BY_STD.items()}