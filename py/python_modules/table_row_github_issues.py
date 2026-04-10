from __future__ import annotations

from dataclasses import dataclass
from typing import Final

REPO_OWNER: Final = "bdenckla"
REPO_NAME: Final = "holman-ketiv-qere"

ISSUE_LABEL_TO_TAG: Final[dict[str, str]] = {
    "QyV": "qyv",
    "ḥolam he": "holam-he",
    "בו״א sans א": "boa-sans-aleph",
    "rafeh": "rafe",
}

ISSUE_TAG_DISPLAY_TEXT: Final[dict[str, str]] = {
    "holam-he": "ḥolam he",
    "qyv": "QyV",
    "boa-sans-aleph": "בו״א sans א",
    "rafe": "rafe",
}


@dataclass(frozen=True)
class RowGitHubIssueMetadata:
    issue_number: int
    is_closed: bool
    tags: tuple[str, ...] = ()


ROW_GITHUB_ISSUES: dict[str, RowGitHubIssueMetadata] = {
    "1": RowGitHubIssueMetadata(issue_number=12, is_closed=False, tags=()),
    "2": RowGitHubIssueMetadata(issue_number=23, is_closed=False, tags=()),
    "3": RowGitHubIssueMetadata(issue_number=19, is_closed=False, tags=()),
    "4": RowGitHubIssueMetadata(issue_number=7, is_closed=False, tags=("qyv",)),
    "5": RowGitHubIssueMetadata(issue_number=21, is_closed=False, tags=()),
    "6": RowGitHubIssueMetadata(issue_number=17, is_closed=False, tags=("qyv",)),
    "7": RowGitHubIssueMetadata(issue_number=22, is_closed=False, tags=("qyv",)),
    "8": RowGitHubIssueMetadata(issue_number=10, is_closed=False, tags=("qyv",)),
    "9": RowGitHubIssueMetadata(issue_number=9, is_closed=False, tags=("qyv",)),
    "10": RowGitHubIssueMetadata(issue_number=5, is_closed=False, tags=("qyv",)),
    "11": RowGitHubIssueMetadata(issue_number=15, is_closed=False, tags=("qyv",)),
    "12": RowGitHubIssueMetadata(
        issue_number=8, is_closed=False, tags=("boa-sans-aleph",)
    ),
    "13": RowGitHubIssueMetadata(issue_number=4, is_closed=False, tags=("rafe",)),
    "14": RowGitHubIssueMetadata(issue_number=11, is_closed=False, tags=("rafe",)),
    "15": RowGitHubIssueMetadata(issue_number=20, is_closed=False, tags=("qyv",)),
    "16": RowGitHubIssueMetadata(issue_number=14, is_closed=False, tags=("qyv",)),
    "17": RowGitHubIssueMetadata(issue_number=13, is_closed=False, tags=("qyv",)),
    "18": RowGitHubIssueMetadata(issue_number=6, is_closed=False, tags=("qyv",)),
    "19": RowGitHubIssueMetadata(issue_number=16, is_closed=False, tags=("qyv",)),
    "20": RowGitHubIssueMetadata(issue_number=18, is_closed=False, tags=("qyv",)),
    "21": RowGitHubIssueMetadata(issue_number=40, is_closed=False, tags=("holam-he",)),
    "22": RowGitHubIssueMetadata(issue_number=27, is_closed=False, tags=("holam-he",)),
    "23": RowGitHubIssueMetadata(issue_number=37, is_closed=False, tags=()),
    "24": RowGitHubIssueMetadata(issue_number=34, is_closed=False, tags=("qyv",)),
    "25": RowGitHubIssueMetadata(issue_number=24, is_closed=False, tags=()),
    "26": RowGitHubIssueMetadata(issue_number=43, is_closed=False, tags=()),
    "27": RowGitHubIssueMetadata(
        issue_number=35, is_closed=False, tags=("boa-sans-aleph",)
    ),
    "28": RowGitHubIssueMetadata(issue_number=25, is_closed=False, tags=("qyv",)),
    "29": RowGitHubIssueMetadata(issue_number=26, is_closed=False, tags=("qyv",)),
    "30": RowGitHubIssueMetadata(issue_number=28, is_closed=False, tags=("qyv",)),
    "31": RowGitHubIssueMetadata(issue_number=29, is_closed=False, tags=("qyv",)),
    "32": RowGitHubIssueMetadata(issue_number=32, is_closed=False, tags=("qyv",)),
    "33": RowGitHubIssueMetadata(issue_number=33, is_closed=False, tags=()),
    "34": RowGitHubIssueMetadata(issue_number=41, is_closed=False, tags=("holam-he",)),
    "35": RowGitHubIssueMetadata(issue_number=31, is_closed=False, tags=("qyv",)),
    "36": RowGitHubIssueMetadata(issue_number=42, is_closed=False, tags=("holam-he",)),
    "37": RowGitHubIssueMetadata(issue_number=36, is_closed=True, tags=()),
    "38": RowGitHubIssueMetadata(issue_number=30, is_closed=False, tags=("qyv",)),
    "39": RowGitHubIssueMetadata(issue_number=39, is_closed=False, tags=()),
    "40": RowGitHubIssueMetadata(issue_number=38, is_closed=False, tags=("qyv",)),
    "41": RowGitHubIssueMetadata(issue_number=48, is_closed=False, tags=("qyv",)),
    "42": RowGitHubIssueMetadata(issue_number=61, is_closed=False, tags=()),
    "43": RowGitHubIssueMetadata(issue_number=46, is_closed=False, tags=("qyv",)),
    "44": RowGitHubIssueMetadata(
        issue_number=47, is_closed=False, tags=("boa-sans-aleph",)
    ),
    "45": RowGitHubIssueMetadata(issue_number=45, is_closed=False, tags=()),
    "46": RowGitHubIssueMetadata(issue_number=44, is_closed=False, tags=("qyv",)),
    "47": RowGitHubIssueMetadata(issue_number=49, is_closed=False, tags=("qyv",)),
    "48": RowGitHubIssueMetadata(issue_number=52, is_closed=True, tags=("qyv",)),
    "49": RowGitHubIssueMetadata(issue_number=63, is_closed=False, tags=("holam-he",)),
    "50": RowGitHubIssueMetadata(issue_number=51, is_closed=True, tags=("qyv",)),
    "51": RowGitHubIssueMetadata(issue_number=57, is_closed=False, tags=("qyv",)),
    "52": RowGitHubIssueMetadata(issue_number=53, is_closed=False, tags=("qyv",)),
    "53": RowGitHubIssueMetadata(issue_number=56, is_closed=False, tags=("qyv",)),
    "54": RowGitHubIssueMetadata(issue_number=59, is_closed=False, tags=("qyv",)),
    "55": RowGitHubIssueMetadata(issue_number=55, is_closed=False, tags=("qyv",)),
    "56": RowGitHubIssueMetadata(issue_number=62, is_closed=False, tags=("qyv",)),
    "57": RowGitHubIssueMetadata(issue_number=60, is_closed=False, tags=("qyv",)),
    "58": RowGitHubIssueMetadata(issue_number=54, is_closed=False, tags=("qyv",)),
    "59": RowGitHubIssueMetadata(issue_number=50, is_closed=False, tags=("qyv",)),
    "60": RowGitHubIssueMetadata(issue_number=58, is_closed=False, tags=("qyv",)),
    "61": RowGitHubIssueMetadata(issue_number=64, is_closed=False, tags=("qyv",)),
    "62": RowGitHubIssueMetadata(issue_number=69, is_closed=False, tags=("qyv",)),
    "63": RowGitHubIssueMetadata(issue_number=68, is_closed=False, tags=("qyv",)),
    "64": RowGitHubIssueMetadata(issue_number=74, is_closed=False, tags=("qyv",)),
    "65": RowGitHubIssueMetadata(issue_number=75, is_closed=False, tags=("qyv",)),
    "66": RowGitHubIssueMetadata(issue_number=80, is_closed=False, tags=("qyv",)),
    "67": RowGitHubIssueMetadata(issue_number=70, is_closed=False, tags=("qyv",)),
    "68": RowGitHubIssueMetadata(issue_number=66, is_closed=False, tags=("qyv",)),
    "69": RowGitHubIssueMetadata(issue_number=73, is_closed=False, tags=("qyv",)),
    "70": RowGitHubIssueMetadata(issue_number=76, is_closed=False, tags=("qyv",)),
    "71": RowGitHubIssueMetadata(issue_number=65, is_closed=False, tags=("qyv",)),
    "72": RowGitHubIssueMetadata(issue_number=78, is_closed=False, tags=("qyv",)),
    "73": RowGitHubIssueMetadata(issue_number=77, is_closed=True, tags=("qyv",)),
    "74": RowGitHubIssueMetadata(issue_number=79, is_closed=True, tags=("rafe",)),
    "75": RowGitHubIssueMetadata(issue_number=71, is_closed=False, tags=("holam-he",)),
    "76": RowGitHubIssueMetadata(issue_number=72, is_closed=True, tags=("holam-he",)),
    "77": RowGitHubIssueMetadata(issue_number=67, is_closed=False, tags=()),
}


def issue_url_from_number(issue_number: int) -> str:
    return f"https://github.com/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}"


def row_github_issue_metadata(row_number: str) -> RowGitHubIssueMetadata | None:
    return ROW_GITHUB_ISSUES.get(str(row_number))


def require_row_github_issue_metadata(row_number: str) -> RowGitHubIssueMetadata:
    metadata = row_github_issue_metadata(row_number)
    if metadata is None:
        raise KeyError(f"missing GitHub issue metadata for table row {row_number}")
    return metadata


def row_github_issue_number(row_number: str) -> int | None:
    metadata = row_github_issue_metadata(row_number)
    if metadata is None:
        return None
    return metadata.issue_number


def row_github_issue_url(row_number: str) -> str | None:
    issue_number = row_github_issue_number(row_number)
    if issue_number is None:
        return None
    return issue_url_from_number(issue_number)


def row_github_issue_is_closed(row_number: str) -> bool | None:
    metadata = row_github_issue_metadata(row_number)
    if metadata is None:
        return None
    return metadata.is_closed


def row_github_issue_tags(row_number: str) -> tuple[str, ...]:
    metadata = row_github_issue_metadata(row_number)
    if metadata is None:
        return ()
    return metadata.tags
