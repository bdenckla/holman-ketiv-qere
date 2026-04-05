from __future__ import annotations

import unittest

from python_modules.extract_docx_notes import apply_notes_fixes, split_notes_components


class ExtractDocxNotesTests(unittest.TestCase):
    def test_row_37_targeted_fix_uses_explicit_ketiv_qere_pair(self) -> None:
        row_data = {
            "row_number": 37,
            "notes": "MAM - No Comments | UXLC - מַה־לִּי־פֹה֙ מי־לי־",
        }

        apply_notes_fixes(row_data)

        self.assertEqual(
            row_data["notes"],
            "MAM - No Comments | UXLC - מי־לי־ מַה־לִּי־",
        )
        self.assertEqual(
            row_data["notes_orig"],
            "MAM - No Comments | UXLC - מַה־לִּי־פֹה֙ מי־לי־",
        )

    def test_split_notes_components_returns_fixed_row_37_uxlc_text(self) -> None:
        notes_uxlc, notes_uxlc_yatir, notes_haketer = split_notes_components(
            "MAM - No Comments | UXLC - מי־לי־ מַה־לִּי־"
        )

        self.assertEqual(notes_uxlc, "מי־לי־ מַה־לִּי־")
        self.assertIsNone(notes_uxlc_yatir)
        self.assertIsNone(notes_haketer)


if __name__ == "__main__":
    unittest.main()