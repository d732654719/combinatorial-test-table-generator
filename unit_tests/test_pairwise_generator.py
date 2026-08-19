import unittest

from combinatorial_test_table_generator.input_schema import validate_request
from combinatorial_test_table_generator.models import Factor
from combinatorial_test_table_generator.pairwise_covering_generator import (
    generate_pairwise,
)
from combinatorial_test_table_generator.pairwise_coverage_validator import (
    verify_pairwise_coverage,
)


def make_request(level_counts):
    return validate_request(
        {
            "mode": "pairwise",
            "strength": 2,
            "factors": [
                {
                    "name": f"因子{factor_index}",
                    "levels": [
                        f"水平{level_index}" for level_index in range(level_count)
                    ],
                }
                for factor_index, level_count in enumerate(level_counts)
            ],
        }
    )


class PairwiseGeneratorTests(unittest.TestCase):
    def assertFullyCovered(self, level_counts):
        result = generate_pairwise(make_request(level_counts))
        self.assertEqual(result.coverage.coverage_rate, 1.0)
        self.assertEqual(result.coverage.uncovered_combinations, ())
        self.assertEqual(
            result.coverage.required_combinations,
            sum(
                first_count * second_count
                for first_index, first_count in enumerate(level_counts)
                for second_count in level_counts[first_index + 1 :]
            ),
        )

    def test_two_factors(self):
        self.assertFullyCovered([2, 3])

    def test_mixed_level_counts(self):
        self.assertFullyCovered([2, 3, 4, 5])

    def test_v01_upper_bound(self):
        self.assertFullyCovered([10] * 8)

    def test_same_input_produces_same_result(self):
        request = make_request([3, 4, 2, 5])

        first = generate_pairwise(request).to_dict()
        second = generate_pairwise(request).to_dict()

        self.assertEqual(first, second)

    def test_case_ids_are_stable_and_padded(self):
        result = generate_pairwise(make_request([2, 2, 2]))

        self.assertEqual(result.test_cases[0]["case_id"], "case_001")
        self.assertEqual(
            result.test_cases[-1]["case_id"], f"case_{result.case_count:03d}"
        )

    def test_validator_reports_missing_combinations(self):
        factors = (
            Factor("A", ("A0", "A1")),
            Factor("B", ("B0", "B1")),
        )

        coverage = verify_pairwise_coverage([(0, 0)], factors)

        self.assertEqual(coverage.required_combinations, 4)
        self.assertEqual(coverage.covered_combinations, 1)
        self.assertEqual(coverage.coverage_rate, 0.25)
        self.assertEqual(len(coverage.uncovered_combinations), 3)


if __name__ == "__main__":
    unittest.main()
