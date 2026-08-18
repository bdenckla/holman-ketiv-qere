"""Resolve the holman-ketiv-qere DATA root, and the subtrees this repo's code reads and writes.

THIS MODULE IS DELIBERATELY TWO-ROOTED, and that is the whole point of its
existence.  Today the code and the data are one directory, so the distinction
buys nothing at run time; the Python is to move into MAM-basics (Phase 3 of
``MAM-basics/doc/PLAN-evacuate-python-from-holman-ketiv-qere.md``) while the
corpus and the Pages site stay here, and then the two roots name different
directories:

  * the CODE root is ``mb_cmn.paths.repo_root()`` -- what ``py/`` is under, what
    ``git`` and ``gh`` act on, what the source lints scan;
  * the DATA root is ``hkq_data_root()`` below -- this repo's ``gh-pages/``,
    ``out/``, ``docs-not-served/``, ``emails/``, ``data/``, ``io/``, ``assets/``
    and gitignored ``.novc/``.

Naming them apart BEFORE the move is what makes the move provable.  While the
code still runs here, this repo's 335 tracked artifacts are an oracle: change a
path, regenerate, and a diff is a bug one change away from its cause.  After the
move a path bug is indistinguishable from a move bug.  Phase 1 of that plan is
this file plus its call sites, and the move itself then changes exactly one line,
the body of ``hkq_data_root()``, because no other module composes a data path off
anything but this function.

What this replaces is not, mostly, cwd-relative literals -- ``main_just_render_table``
had the only two -- but ``Path(__file__).resolve().parents[N]`` walks that were
already cwd-independent and still conflated the two roots.  Each of the six
generators had one, spelled ``REPO_ROOT``, and composed both data paths
(``REPO_ROOT / "gh-pages"``) and sibling-repo paths (``REPO_ROOT.parent /
"MAM-parsed"``) off it.  After the move the first kind resolves silently into
MAM-basics' tree, which is the failure this module exists to prevent.

``mb_cmn.paths`` owns sibling-repo resolution and its ``REPO_<NAME>_DIR`` /
``REPOS_ROOT`` override chain; this module delegates rather than keeping a second
copy of it.  ``py/uxlc_paths.py`` beside this file is the same shape for
UXLC-utils' corpus, written for that repo's Phase 1 and now living in MAM-basics.
"""

from __future__ import annotations

from pathlib import Path

from mb_cmn import paths

DATA_REPO_NAME = "holman-ketiv-qere"

REVIEW_DOCX_NAME = "Review of Qere and Kethib readings in the Aleppo and Leningrad.docx"


def hkq_data_root() -> Path:
    """Path to the holman-ketiv-qere corpus this code reads and writes.

    The one line that changes when the Python moves out -- see the module
    docstring.  Today the code lives here, so this is the repo root; afterwards it
    becomes ``paths.require_sibling(DATA_REPO_NAME, paths.sibling_repo(DATA_REPO_NAME))``.
    """
    return paths.repo_root()


def gh_pages_dir() -> Path:
    """Published-HTML tree, 300 tracked files, served at bdenckla.github.io/holman-ketiv-qere.

    THE DEPLOY ROOT, not any one report under it: ``.github/workflows/pages.yml``
    hands exactly this directory to ``upload-pages-artifact``.

    Its two largest subdirectories are image trees.  ``uxlc_img`` has an accessor of
    its own below, three modules naming it.  ``img``, the 154 images extracted from
    the ketiv/qere review docx, deliberately has none: ``main_extract_docx_and_render_table``
    derives it from whatever ``--served-docs-dir`` resolved to, so that overriding the
    one moves the other with it.  That tree is also WRITE-ONCE -- ``export_images``
    raises rather than overwrite an image whose bytes differ -- so a full regeneration
    leaves all 154 alone, and a wrong root there surfaces as 154 files appearing where
    nothing tracks them rather than as a diff.
    """
    return hkq_data_root() / "gh-pages"


def email_img_dir() -> Path:
    """PNGs attached to Holman's correction emails (``<gh_pages_dir>/uxlc_img``), 135 tracked.

    Written by the ingest step from the untracked ``.eml`` files and read by the
    render step, which is why both name it.  Distinct from ``docx_img_dir`` above:
    different source, different report, and these are rewritten on every ingest.
    """
    return gh_pages_dir() / "uxlc_img"


def out_dir() -> Path:
    """Generated-report tree, 2 tracked files: the two phenomenon searches' JSON.

    NOT ``paths.out_dir()``, which is the CODE repo's tree.  The two name the same
    directory only while the code still lives here.
    """
    return hkq_data_root() / "out"


def docs_not_served_dir() -> Path:
    """Extracted source data that Pages does not serve (``<data_root>/docs-not-served``), 4 tracked.

    Three are generated -- ``introduction.md``, ``table_data.json``,
    ``uxlc_corrections.json``; ``table_data_fields.md`` is hand-authored and
    documents the third.
    """
    return hkq_data_root() / "docs-not-served"


def emails_dir() -> Path:
    """The address-free derivative of Holman's emails (``<data_root>/emails``), 26 tracked.

    A body ``.txt`` and a metadata ``.json`` per message, 13 messages.  This repo is
    public and the ``.eml`` files have the correspondents' addresses, so the ingest
    step redacts as it reads and everything downstream reads this tree instead --
    see ``CLAUDE.md``'s section on that boundary.
    """
    return hkq_data_root() / "emails"


def data_dir() -> Path:
    """What the sibling UXLC-utils clone says about each atom (``<data_root>/data``), 2 tracked.

    ``uxlc_atom_locations.json`` and ``uxlc_standard_atoms.json``, both written by
    ``main_estimate_uxlc_locations`` and read by the render step.  Tracked so that a
    fresh clone can render the report without the ~11 MB of UXLC core XML this repo
    does not track.
    """
    return hkq_data_root() / "data"


def io_dir() -> Path:
    """Hand-curated input that a script also rewrites (``<data_root>/io``), 1 tracked."""
    return hkq_data_root() / "io"


def assets_dir() -> Path:
    """Authored CSS and JS templates the render steps copy into ``gh-pages`` (4 tracked).

    Input to a generator rather than output of one, and DATA rather than code
    despite being source text: these are the templates whose published copies sit in
    ``gh_pages_dir()``, and they stay with the site.  ``CLAUDE.md`` records that they
    use ``light-dark()`` pairs rather than a ``prefers-color-scheme`` block.
    """
    return hkq_data_root() / "assets"


def novc_dir() -> Path:
    """Gitignored scratch tree (``<data_root>/.novc``)."""
    return hkq_data_root() / ".novc"


def eml_dir() -> Path:
    """The untracked mailbox the ingest step reads (``<novc_dir>/eml``), 13 messages.

    Deliberately outside version control -- a ``.eml`` header has Holman's address,
    Chris Kimball's and Ben's.  Under ``.novc`` for that reason and not for size.
    """
    return novc_dir() / "eml"


def review_docx_path() -> Path:
    """The ketiv/qere review document, the source of the 77-row table."""
    return hkq_data_root() / REVIEW_DOCX_NAME


def table_data_json_path() -> Path:
    """The extracted review table (``<docs_not_served_dir>/table_data.json``).

    Exactly 77 rows, a fixed project scope rather than a current count, so a
    regeneration that changes the row count is a failure and not a finding.
    """
    return docs_not_served_dir() / "table_data.json"


def findings_html_path() -> Path:
    """The finding-filterable report built from ``table_data_json_path``."""
    return gh_pages_dir() / "table_data_findings.html"


def row_github_issues_path() -> Path:
    """Checked-in issue state and labels per review row (``<io_dir>/table_row_github_issues.json``).

    Refreshed from live GitHub by ``refresh_table_row_github_issues``, which names
    ``bdenckla/holman-ketiv-qere`` to ``gh --repo`` outright rather than letting the
    working directory pick a tracker.  That stays true after the move.
    """
    return io_dir() / "table_row_github_issues.json"


def uxlc_corrections_json_path() -> Path:
    """The extracted corrections (``<docs_not_served_dir>/uxlc_corrections.json``).

    Tracked so that regenerating it and reading the diff is the test: a parse that
    changes silently cannot.
    """
    return docs_not_served_dir() / "uxlc_corrections.json"


def uxlc_corrections_html_path() -> Path:
    """The suggested-UXLC-corrections report (``<gh_pages_dir>/uxlc_corrections.html``)."""
    return gh_pages_dir() / "uxlc_corrections.html"


def mam_qere_words_path() -> Path:
    """MAM-basics' qere word list, the sanity check the holam-he search compares against.

    THE ONE PATH WHOSE KIND FLIPS AT THE MOVE, and the reason it has an accessor of
    its own.  Today MAM-basics is a sibling of this repo; after the move it is the
    repo the code lives in, so this becomes ``paths.out_dir() / "mam-qere-words.json"``
    -- the CODE root's tree, where every other accessor here wants the DATA root's.
    """
    return paths.sibling_repo("MAM-basics") / "out" / "mam-qere-words.json"
