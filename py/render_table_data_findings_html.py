from __future__ import annotations

import argparse
from pathlib import Path

from python_modules.render_table_data_findings_html import render_table_data_findings_html


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a finding-filterable HTML report from docs/table_data.json."
    )
    parser.add_argument(
        "--table-json-path",
        type=Path,
        default=Path("docs/table_data.json"),
        help="Path to table_data.json input.",
    )
    parser.add_argument(
        "--output-html-path",
        type=Path,
        default=Path("docs/table_data_findings.html"),
        help="Path for generated HTML output.",
    )
    args = parser.parse_args()

    output_path = render_table_data_findings_html(
        table_json_path=args.table_json_path,
        output_html_path=args.output_html_path,
    )
    print(output_path.as_posix())


if __name__ == "__main__":
    main()
