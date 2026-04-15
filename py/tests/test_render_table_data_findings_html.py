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

    def test_renders_simple_letter_descriptions_for_non_qyv_non_holam_rows(
        self,
    ) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 13,
                        "verse": "Joshua 1:1.1",
                        "word": "הִיא",
                        "finding": "Finding A",
                        "notes-UXLC": "הוא הִוא",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "13": {
                "issue_number": 13,
                "is_closed": False,
                "tags": [],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn(
            '<div class="note-line"><span class="label">MAM vs UXLC ketiv letters:</span> <span>replace yod with vav</span></div>',
            main_html,
        )
        self.assertIn(
            '<div class="note-line"><span class="label">MAM vs UXLC qere:</span> <span>replace yod with vav</span></div>',
            main_html,
        )

    def test_suppresses_qere_note_when_qere_exactly_matches_mam(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 15,
                        "verse": "Joshua 1:1.1",
                        "word": "לִי",
                        "finding": "Finding A",
                        "notes-UXLC": "לו לִי",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "15": {
                "issue_number": 15,
                "is_closed": False,
                "tags": [],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn(
            '<div class="note-line"><span class="label">MAM vs UXLC ketiv letters:</span> <span>replace yod with vav</span></div>',
            main_html,
        )
        self.assertNotIn("MAM vs UXLC qere:", main_html)

    def test_prefers_pointing_aware_xaser_malei_description_for_single_insert(
        self,
    ) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 39,
                        "verse": "Jeremiah 5:6.21",
                        "word": "מְשֻׁבוֹתֵיהֶֽם׃",
                        "finding": "Finding A",
                        "notes-UXLC": "משבותיהם מְשׁוּבוֹתֵיהֶֽם׃",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "39": {
                "issue_number": 39,
                "is_closed": False,
                "tags": [],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn("replace qubuts with shuruq", main_html)
        self.assertNotIn("add vav after shin", main_html)

    def test_renders_xaser_malei_description_when_qere_diff_is_not_one_grapheme_edit(
        self,
    ) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 25,
                        "verse": "2Chronicles 24:25.6",
                        "word": "בְּמַחֲלֻיִ֣ים",
                        "finding": "Finding A",
                        "notes-UXLC": "במחליים בְּמַחֲלוּיִ֣ם",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "25": {
                "issue_number": 25,
                "is_closed": False,
                "tags": [],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn(
            "replace qubuts with shuruq; replace ḥiriq-yod with ḥiriq",
            main_html,
        )

    def test_renders_compact_ketiv_note_for_adjacent_transposition(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 1,
                        "verse": "Joshua 3:4.5",
                        "word": "וּבֵנָ֔יו",
                        "finding": "Finding A",
                        "notes-UXLC": "ובינו וּבֵינָ֔יו",
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
            '<div class="note-line"><span class="label">MAM vs UXLC ketiv letters:</span> <span>swap nun and yod</span></div>',
            main_html,
        )
        self.assertIn(
            '<div class="note-line"><span class="label">MAM vs UXLC qere:</span> <span>replace tsere with tsere-yod</span></div>',
            main_html,
        )

    def test_renders_xaser_malei_note_with_extra_mark_detail(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 26,
                        "verse": "Job 1:4.11",
                        "word": "אַחְיֹתֵיהֶ֔ם",
                        "finding": "Finding A",
                        "notes-UXLC": "אחיתיהם אַחְיֽוֹתֵיהֶ֔ם",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "26": {
                "issue_number": 26,
                "is_closed": False,
                "tags": [],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn(
            '<div class="note-line"><span class="label">MAM vs UXLC qere:</span> <span>replace ḥolam with ḥolam-vav (also add meteg on 1st yod)</span></div>',
            main_html,
        )

    def test_renders_fallback_ketiv_note_for_non_simple_difference(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 1,
                        "verse": "Joshua 3:4.5",
                        "word": "אַבְגָ֔ד",
                        "finding": "Finding A",
                        "notes-UXLC": "גבדא אַבְגָ֔ד",
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
            '<div class="note-line"><span class="label">MAM vs UXLC ketiv letters:</span> <bdi class="pointed-heb">MAM אַבְגָ֔ד; UXLC ketiv גבדא</bdi></div>',
            main_html,
        )

    def test_renders_simple_mark_description_for_non_qyv_non_holam_rows(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 14,
                        "verse": "Joshua 1:1.1",
                        "word": "דָּבָר",
                        "finding": "Finding A",
                        "notes-UXLC": "דבר דָּבַר",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "14": {
                "issue_number": 14,
                "is_closed": False,
                "tags": ["rafeh"],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertNotIn("MAM vs UXLC ketiv letters:", main_html)
        self.assertIn(
            '<div class="note-line"><span class="label">MAM vs UXLC qere:</span> <span>on bet, qamats in MAM → pataḥ in UXLC qere</span></div>',
            main_html,
        )

    def test_skips_simple_descriptions_for_qyv_rows(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 4,
                        "verse": "1Samuel 2:9.2",
                        "word": "חֲסִידָו֙",
                        "finding": "Finding A",
                        "notes-UXLC": "חסידו חֲסִידָיו֙",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "4": {
                "issue_number": 7,
                "is_closed": False,
                "tags": ["qyv"],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertNotIn("MAM vs UXLC ketiv letters:", main_html)
        self.assertNotIn("MAM vs UXLC qere:", main_html)

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
                        "word": "חֲסִידָו֙",
                        "finding": "Finding B",
                        "notes-UXLC": "חסידו חֲסִידָיו֙",
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
        self.assertIn('href="table_data_findings.html">Active</a>', suppressed_html)
        self.assertIn(
            'href="table_data_findings_suppressed.html">Suppressed</a>', main_html
        )
        self.assertNotIn(">Review<", main_html)
        self.assertNotIn(">Review<", suppressed_html)
        self.assertNotIn("Source: sample.docx", main_html)
        self.assertNotIn("Source: sample.docx", suppressed_html)
        self.assertIn("Closed issues only", suppressed_html)
        self.assertIn("Total Records", main_html)
        self.assertIn("Visible/Filtered-out records", main_html)
        self.assertIn('id="visible-filtered-count">2/0</div>', main_html)
        self.assertNotIn("Rows on Page", main_html)
        self.assertNotIn('<h2 class="section-title">Filter</h2>', main_html)
        self.assertNotIn("filter-btn", main_html)
        self.assertNotIn("Unique Finding Values", main_html)
        self.assertNotIn("Summary by finding", main_html)
        self.assertNotIn("<th>Finding</th>", main_html)
        self.assertNotIn("<th>Count</th>", main_html)
        self.assertIn("no issue tag</td><td>1", main_html)
        self.assertIn("no issue tag</td><td>1", suppressed_html)
        self.assertRegex(
            main_html,
            re.compile(
                r'<article id="row01".*?<span class="category-badges">.*?Finding A.*?no issue tag.*?</span>',
                re.DOTALL,
            ),
        )
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
                        "word": "חֲסִידָו֙",
                        "finding": "Finding A",
                        "notes-UXLC": "חסידו חֲסִידָיו֙",
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
                        "verse": "Psalms 42:9.6",
                        "word": "שִׁירֹ֣ה",
                        "finding": "Finding D",
                        "notes-UXLC": "שירה שִׁיר֣וֹ",
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
                            "argument_text": "חֲסִידָו֙",
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
                "tags": ["rafeh"],
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

        self.assertRegex(
            main_html,
            re.compile(
                r'<div class="summary-columns">.*?'
                r'<section class="summary-group"><h2 class="summary-group-title">Aleppo notation</h2><table class="summary">.*?'
                r"Finding A</td><td>1.*?Finding B</td><td>1.*?Finding C</td><td>1.*?Finding D</td><td>1.*?</table></section>.*?"
                r'<section class="summary-group"><h2 class="summary-group-title">Issue tags</h2><table class="summary">.*?'
                r"ḥolam he</td><td>1.*?QyV</td><td>1.*?בו״א sans א</td><td>1.*?rafeh</td><td>1.*?no issue tag</td><td>0|1.*?</table></section>.*?"
                r'<section class="summary-group"><h2 class="summary-group-title">MPP</h2><table class="summary">.*?'
                r"Has matching MPP template</td><td>1.*?</table></section>",
                re.DOTALL,
            ),
        )
        self.assertIn(
            'data-filter-id="issue-tag-rafeh"><td><span class="cat-swatch cat-issue-tag-rafeh"></span>rafeh</td><td>1</td></tr>',
            main_html,
        )
        self.assertIn("Has matching MPP template</td><td>1", main_html)
        self.assertIn("QyV</td><td>1", main_html)
        self.assertIn("בו״א sans א</td><td>1", main_html)
        self.assertIn("rafeh</td><td>1", main_html)
        self.assertIn("ḥolam he</td><td>1", main_html)
        self.assertIn(
            'MAM Word:</span><bdi class="pointed-heb">חֲסִידָו֙</bdi>',
            main_html,
        )
        self.assertNotIn(
            'MAM Word (from latest MPP):</span><bdi class="pointed-heb">חֲסִידָו֙</bdi>',
            main_html,
        )
        self.assertRegex(
            main_html,
            re.compile(
                r'<article id="row04".*?<span class="category-badges">.*?Finding A.*?Has matching MPP template.*?QyV.*?</span>',
                re.DOTALL,
            ),
        )
        self.assertNotIn(
            'MPP matching template arg (q[1]):</span><bdi class="pointed-heb">חֲסִידָו֙</bdi>',
            main_html,
        )
        self.assertRegex(
            main_html,
            re.compile(
                r'<article id="row13".*?<span class="category-badges">.*?Finding C.*?rafeh.*?</span>',
                re.DOTALL,
            ),
        )
        self.assertRegex(
            main_html,
            re.compile(
                r'<article id="row13".*?MAM Word:</span><bdi class="pointed-heb">ג</bdi>.*?UXLC:</span><bdi class="pointed-heb">ג</bdi>',
                re.DOTALL,
            ),
        )
        self.assertRegex(
            main_html,
            re.compile(
                r'<article id="row21".*?<span class="category-badges">.*?Finding D.*?ḥolam he.*?</span>',
                re.DOTALL,
            ),
        )
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

    def test_shows_explicit_docx_and_latest_mpp_labels_when_words_differ(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 13,
                        "verse": "2Samuel 11:24.1",
                        "word": "וַיֹּר֨אוּ",
                        "finding": "Finding C",
                        "notes-UXLC": "ויראו וַיֹּר֨וּ",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [
                {
                    "row_number": 13,
                    "matching_template_args_in_mpp_verse": [
                        {
                            "template_name": 'קו"כ-אם',
                            "argument_key": "1",
                            "argument_text": "וַיֹּר֨אֿוּ",
                        }
                    ],
                }
            ],
        }

        row_github_issues_payload = {
            "13": {
                "issue_number": 4,
                "is_closed": False,
                "tags": ["rafeh"],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn(
            'MAM Word (from docx):</span><bdi class="pointed-heb">וַיֹּר֨אוּ</bdi>',
            main_html,
        )
        self.assertIn(
            'MAM Word (from latest MPP):</span><bdi class="pointed-heb">וַיֹּר֨אֿוּ</bdi>',
            main_html,
        )
        self.assertRegex(
            main_html,
            re.compile(
                r'<article id="row13".*?MAM Word \(from docx\):</span><bdi class="pointed-heb">וַיֹּר֨אוּ</bdi>.*?MAM Word \(from latest MPP\):</span><bdi class="pointed-heb">וַיֹּר֨אֿוּ</bdi>',
                re.DOTALL,
            ),
        )
        self.assertIn(
            '</div>\n<div class="note-line"><span class="label">MAM Word (from latest MPP):</span>',
            main_html,
        )
        self.assertNotIn(
            'MPP matching template arg (קו&quot;כ-אם[1]):</span><bdi class="pointed-heb">וַיֹּר֨אֿוּ</bdi>',
            main_html,
        )

    def test_rejects_qyv_tag_when_qere_is_not_yod_before_final_vav(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 4,
                        "verse": "1Samuel 2:9.2",
                        "word": "חֲסִידָו֙",
                        "finding": "Finding A",
                        "notes-UXLC": "חסידו חֲסִידָו֙",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "4": {
                "issue_number": 7,
                "is_closed": False,
                "tags": ["qyv"],
            }
        }

        with self.assertRaisesRegex(
            ValueError,
            r"row 4 .*violates expected qere.*tagged QyV in findings renderer",
        ):
            self._render(payload, row_github_issues_payload)

    def test_accepts_qyv_tag_with_final_punctuation(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 55,
                        "verse": "Ezekiel 40:26.13",
                        "word": "אֵילָֽו׃",
                        "finding": "Finding A",
                        "notes-UXLC": "אילו אֵילָֽיו׃",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "55": {
                "issue_number": 55,
                "is_closed": False,
                "tags": ["qyv"],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn('id="row55"', main_html)

    def test_accepts_qyv_tag_with_meteg_difference(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 18,
                        "verse": "2Samuel 24:14.14",
                        "word": "רַחֲמָ֔ו",
                        "finding": "Finding A",
                        "notes-UXLC": "רחמו רַֽחֲמָ֔יו",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "18": {
                "issue_number": 6,
                "is_closed": False,
                "tags": ["qyv"],
            }
        }

        main_html, _suppressed_html, _js = self._render(
            payload,
            row_github_issues_payload,
        )

        self.assertIn('id="row18"', main_html)

    def test_rejects_missing_qyv_tag_for_matching_row(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 4,
                        "verse": "1Samuel 2:9.2",
                        "word": "חֲסִידָו֙",
                        "finding": "Finding A",
                        "notes-UXLC": "חסידו חֲסִידָיו֙",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "4": {
                "issue_number": 7,
                "is_closed": False,
                "tags": [],
            }
        }

        with self.assertRaisesRegex(
            ValueError,
            r"row 4 .*matches the QyV definition but is missing the qyv tag",
        ):
            self._render(payload, row_github_issues_payload)

    def test_rejects_holam_he_tag_when_qere_is_not_final_vav(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 34,
                        "verse": "Psalms 42:9.6",
                        "word": "שִׁירֹ֣ה",
                        "finding": "Finding A",
                        "notes-UXLC": "שירה שִׁירֹ֣ה",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "34": {
                "issue_number": 41,
                "is_closed": False,
                "tags": ["holam-he"],
            }
        }

        with self.assertRaisesRegex(
            ValueError,
            r"row 34 .*violates expected qere.*tagged holam-he in findings renderer",
        ):
            self._render(payload, row_github_issues_payload)

    def test_rejects_missing_holam_he_tag_for_matching_row(self) -> None:
        payload = {
            "source_document": "sample.docx",
            "table": {
                "rows": [
                    {
                        "row_number": 34,
                        "verse": "Psalms 42:9.6",
                        "word": "שִׁירֹ֣ה",
                        "finding": "Finding A",
                        "notes-UXLC": "שירה שִׁיר֣וֹ",
                    }
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [],
        }

        row_github_issues_payload = {
            "34": {
                "issue_number": 41,
                "is_closed": False,
                "tags": [],
            }
        }

        with self.assertRaisesRegex(
            ValueError,
            r"row 34 .*matches the holam-he definition but is missing the holam-he tag",
        ):
            self._render(payload, row_github_issues_payload)


if __name__ == "__main__":
    unittest.main()
