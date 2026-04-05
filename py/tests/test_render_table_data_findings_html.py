from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from python_modules.render_table_data_findings_html import render_table_data_findings_html


class RenderTableDataFindingsHtmlTests(unittest.TestCase):
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

        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            table_json_path = docs_dir / "table_data.json"
            output_html_path = docs_dir / "table_data_findings.html"

            table_json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            render_table_data_findings_html(
                table_json_path=table_json_path,
                output_html_path=output_html_path,
            )

            html = output_html_path.read_text(encoding="utf-8")

        self.assertIn(
            '<div class="note-line"><span class="label">UXLC yatir:</span> <span>aleph</span></div>',
            html,
        )
        self.assertNotIn('UXLC yatir:</span><bdi class="pointed-heb">yatir aleph</bdi>', html)

    def test_renders_non_exclusive_mpp_template_filter(self) -> None:
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
                        "row_number": 2,
                        "verse": "1Samuel 2:9.2",
                        "word": "ב",
                        "finding": "Finding B",
                        "notes-UXLC": "ב",
                    },
                ]
            },
            "mam_plus_rows_matching_mpp_verse_template_arg": [
                {
                    "row_number": 1,
                    "matching_template_args_in_mpp_verse": [
                        {
                            "template_name": "q",
                            "argument_key": "1",
                            "argument_text": "א",
                        }
                    ],
                },
                {
                    "row_number": 2,
                    "matching_template_args_in_mpp_verse": [],
                },
            ],
        }

        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            table_json_path = docs_dir / "table_data.json"
            output_html_path = docs_dir / "table_data_findings.html"

            table_json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            render_table_data_findings_html(
                table_json_path=table_json_path,
                output_html_path=output_html_path,
            )

            html = output_html_path.read_text(encoding="utf-8")
            js = output_html_path.with_suffix(".js").read_text(encoding="utf-8")

        self.assertIn(
            'data-filter-id="has-mpp-template">Has matching MPP template (1)</button>',
            html,
        )
        self.assertIn(
            '<article id="row01" class="record-card" data-finding-id="f00" data-filter-ids="f00 has-mpp-template">',
            html,
        )
        self.assertIn(
            '<article id="row02" class="record-card" data-finding-id="f01" data-filter-ids="f01">',
            html,
        )
        self.assertIn(
            'Joshua 1:1.1 <a href="https://www.mgketer.org/mikra/6/1/1/mg/106" target="_blank" rel="noopener">mgketer</a> <a href="https://bdenckla.github.io/MAM-with-doc/B1-Joshua.html#c1v1" target="_blank" rel="noopener">MwD</a> <a href="https://he.wikisource.org/wiki/%D7%99%D7%94%D7%95%D7%A9%D7%A2_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D" target="_blank" rel="noopener">MAM-ws</a> <a href="https://github.com/bdenckla/holman-ketiv-qere/issues/12" target="_blank" rel="noopener">issue</a>',
            html,
        )
        self.assertIn(
            '1Samuel 2:9.2 <a href="https://www.mgketer.org/mikra/8/2/1/mg/106" target="_blank" rel="noopener">mgketer</a> <a href="https://bdenckla.github.io/MAM-with-doc/BA-1Samuel.html#c2v9" target="_blank" rel="noopener">MwD</a> <a href="https://he.wikisource.org/wiki/%D7%A9%D7%9E%D7%95%D7%90%D7%9C%20%D7%90_%D7%91/%D7%98%D7%A2%D7%9E%D7%99%D7%9D" target="_blank" rel="noopener">MAM-ws</a> <a href="https://github.com/bdenckla/holman-ketiv-qere/issues/23" target="_blank" rel="noopener">issue</a>',
            html,
        )
        self.assertIn(".filter-btn[data-filter-id]", js)
        self.assertIn("card.dataset.filterIds", js)


if __name__ == "__main__":
    unittest.main()