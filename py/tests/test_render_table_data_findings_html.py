from __future__ import annotations

import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

from python_modules.render_table_data_findings_html import (
    render_table_data_findings_html,
)
from python_modules.table_row_github_issues import reload_row_github_issues


class RenderTableDataFindingsHtmlTests(unittest.TestCase):
    def _render(
        self,
        payload: dict[str, object],
        row_github_issues_payload: dict[str, dict[str, object]],
    ) -> tuple[str, str, str]:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            gh_pages_dir = tmp_path / "gh-pages"
            gh_pages_dir.mkdir(parents=True, exist_ok=True)
            table_json_path = gh_pages_dir / "table_data.json"
            output_html_path = gh_pages_dir / "table_data_findings.html"
            row_github_issues_json_path = tmp_path / "table_row_github_issues.json"

            table_json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            row_github_issues_json_path.write_text(
                json.dumps(
                    row_github_issues_payload,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            try:
                reload_row_github_issues(row_github_issues_json_path)
                render_table_data_findings_html(
                    table_json_path=table_json_path,
                    output_html_path=output_html_path,
                )
            finally:
                reload_row_github_issues()

            main_html = output_html_path.read_text(encoding="utf-8")
            suppressed_html = output_html_path.with_name(
                "table_data_findings_suppressed.html"
            ).read_text(encoding="utf-8")
            js = output_html_path.with_suffix(".js").read_text(encoding="utf-8")

        return main_html, suppressed_html, js

    def test_renders_yatir_note_without_hebrew_styling_for_latin_text(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 1,
                        "verse": "Joshua 1:1.1",
                        "word": "א",
                        "finding": "Finding A",
                        "notes-UXLC": "א",
                        "notes-UXLC-yatir": "yatir aleph",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "1": {
                "issue_number": 12,
                "is_closed": False,
                "tags": [],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn(
            '<div class="note-line"><span class="label">UXLC yatir:</span> <span>aleph</span></div>',
            main_html,
        )
        self.assertNotIn(
            'UXLC yatir:</span><bdi class="pointed-heb">yatir aleph</bdi>',
            main_html,
        )

    def test_renders_page_split_navigation_and_revised_summary_copy(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 1,
                        "verse": "Joshua 1:1.1",
                        "word": "א",
                        "finding": "Finding A",
                        "notes-UXLC": "א",
                    },
                    {
                        "row_number": 4,
                        "verse": "1Samuel 2:9.2",
                        "word": "ב",
                        "finding": "Finding B",
                        "notes-UXLC": "ב",
                    },
                    {
                        "row_number": 37,
                        "verse": "Isaiah 1:1.1",
                        "word": "ג",
                        "finding": "Finding C",
                        "notes-UXLC": "ג",
                    },
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "1": {
                "issue_number": 12,
                "is_closed": False,
                "tags": [],
            },
            "4": {
                "issue_number": 7,
                "is_closed": False,
                "tags": ["qyv"],
            },
            "37": {
                "issue_number": 36,
                "is_closed": True,
                "tags": [],
            },
        }

        main_html, suppressed_html, js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn("<title>Holman k/q</title>", main_html)
        self.assertIn("<h1>Holman ketiv/qere review</h1>", main_html)
        self.assertIn("Visible/Filtered-out records", main_html)
        self.assertIn('id="visible-filtered-count">2/0</div>', main_html)
        self.assertNotIn("Unique Finding Values", main_html)
        self.assertNotIn("Summary by finding", main_html)
        self.assertNotIn("<th>Finding</th>", main_html)
        self.assertNotIn("<th>Count</th>", main_html)
        self.assertIn(
            'href="table_data_findings_suppressed.html">Suppressed</a>', main_html
        )
        self.assertIn('href="table_data_findings.html">Review</a>', suppressed_html)
        self.assertIn("<h1>Suppressed</h1>", suppressed_html)
        self.assertIn('id="row37"', suppressed_html)
        self.assertNotIn('id="row37"', main_html)
        self.assertIn("visible-filtered-count", js)

    def test_renders_non_exclusive_mpp_and_issue_tag_filters(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 4,
                        "verse": "1Samuel 2:9.2",
                        "word": "א",
                        "finding": "Finding A",
                        "notes-UXLC": "א",
                    },
                    {
                        "row_number": 12,
                        "verse": "Joshua 1:2.1",
                        "word": "ב",
                        "finding": "Finding B",
                        "notes-UXLC": "ב",
                    },
                    {
                        "row_number": 13,
                        "verse": "Joshua 1:3.1",
                        "word": "ג",
                        "finding": "Finding C",
                        "notes-UXLC": "ג",
                    },
                    {
                        "row_number": 21,
                        "verse": "Joshua 1:4.1",
                        "word": "ד",
                        "finding": "Finding D",
                        "notes-UXLC": "ד",
                    },
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [
                {
                    "row_number": 4,
                    "matching_template_args_in_mpp_verse": [
                        {
                            "template_name": "q",
                            "argument_key": "1",
                            "argument_text": "א",
                        }
                    ],
                },
                {
                    "row_number": 12,
                    "matching_template_args_in_mpp_verse": [],
                },
                {
                    "row_number": 13,
                    "matching_template_args_in_mpp_verse": [],
                },
                {
                    "row_number": 21,
                    "matching_template_args_in_mpp_verse": [],
                },
            ],
        }

        row_github_issues_payload = {
            "4": {
                "issue_number": 7,
                "is_closed": False,
                "tags": ["qyv"],
            },
            "12": {
                "issue_number": 8,
                "is_closed": False,
                "tags": ["boa-sans-aleph"],
            },
            "13": {
                "issue_number": 4,
                "is_closed": False,
                "tags": ["rafe"],
            },
            "21": {
                "issue_number": 40,
                "is_closed": False,
                "tags": ["holam-he"],
            },
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn("Has matching MPP template (1)", main_html)
        self.assertIn("QyV (1)", main_html)
        self.assertIn("בו״א sans א (1)", main_html)
        self.assertIn("rafe (1)", main_html)
        self.assertIn("ḥolam he (1)", main_html)
        self.assertRegex(
            main_html,
            re.compile(
                r'<article id="row04"[^>]*data-filter-ids="[^"]*has-mpp-template[^"]*issue-tag-qyv[^"]*"'
            ),
        )
        self.assertIn(
            '1Samuel 2:9.2 <a href="https://www.mgketer.org/mikra/8/2/1/mg/106" target="_blank" rel="noopener">mgketer</a> <a href="https://bdenckla.github.io/MAM-with-doc/BA-1Samuel.html#c2v9" target="_blank" rel="noopener">MwD</a> <a href="https://he.wikisource.org/wiki/%D7%A9%D7%9E%D7%95%D7%90%D7%9C%20%D7%90_%D7%91/%D7%98%D7%A2%D7%9E%D7%99%D7%9D" target="_blank" rel="noopener">MAM-ws</a> <a href="https://github.com/bdenckla/holman-ketiv-qere/issues/7" target="_blank" rel="noopener">issue</a>',
            main_html,
        )


if __name__ == "__main__":
    unittest.main()
