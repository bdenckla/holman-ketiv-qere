from __future__ import annotations

import unittest

from python_modules.verify_table_words_in_mam_plus import (
    contains_word_as_hebrew_token,
)


class HebrewTokenMatcherTests(unittest.TestCase):
    def test_exact_match(self) -> None:
        self.assertTrue(contains_word_as_hebrew_token("אֵילָו֙", "אֵילָו֙"))

    def test_no_match_when_embedded_in_larger_hebrew_token(self) -> None:
        self.assertFalse(contains_word_as_hebrew_token("וְאֵילָו֙ם", "אֵילָו֙"))

    def test_space_boundaries_match(self) -> None:
        self.assertTrue(contains_word_as_hebrew_token("לפני אֵילָו֙ אחרי", "אֵילָו֙"))

    def test_ascii_punctuation_boundaries_match(self) -> None:
        self.assertTrue(contains_word_as_hebrew_token("(אֵילָו֙),", "אֵילָו֙"))

    def test_maqaf_boundary_counts_as_separator(self) -> None:
        self.assertTrue(contains_word_as_hebrew_token("אֵילָו֙־וְאֵילָיו", "אֵילָו֙"))

    def test_sof_pasuq_boundary_counts_as_separator(self) -> None:
        self.assertTrue(contains_word_as_hebrew_token("אֵילָו֙׃", "אֵילָו֙"))


if __name__ == "__main__":
    unittest.main()
