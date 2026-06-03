import unittest

from src.aggregator import PhraseAggregator, normalize_phrase


class PhraseAggregatorTest(unittest.TestCase):
    def test_normalize_phrase_removes_punctuation_and_spacing(self):
        self.assertEqual(
            normalize_phrase("  High-Pressure   Leaks! "),
            "high pressure leaks",
        )

    def test_results_are_deterministically_sorted_for_equal_counts(self):
        aggregator = PhraseAggregator()
        aggregator.add("2", {"Mud Pump", "Bit Bounce"})
        aggregator.add("1", {"bit-bounce", "Drilling Parameters"})

        self.assertEqual(
            aggregator.results(min_count=1),
            [
                {
                    "keyword": "Bit Bounce",
                    "count": 2,
                    "file_numbers": ["1", "2"],
                },
                {
                    "keyword": "Drilling Parameters",
                    "count": 1,
                    "file_numbers": ["1"],
                },
                {
                    "keyword": "Mud Pump",
                    "count": 1,
                    "file_numbers": ["2"],
                },
            ],
        )

    def test_display_name_is_deterministic_for_normalized_matches(self):
        aggregator = PhraseAggregator()
        aggregator.add("1", {"High-Pressure Leaks", "high pressure leaks"})

        self.assertEqual(
            aggregator.results(min_count=1),
            [
                {
                    "keyword": "High-Pressure Leaks",
                    "count": 1,
                    "file_numbers": ["1"],
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
