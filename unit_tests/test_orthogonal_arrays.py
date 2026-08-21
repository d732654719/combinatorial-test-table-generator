import json
import unittest
from importlib import resources

from combinatorial_test_table_generator.generator import generate
from combinatorial_test_table_generator.input_schema import (
    InputValidationError,
    validate_request,
)
from combinatorial_test_table_generator.models import Factor
from combinatorial_test_table_generator.orthogonal_array_selector import (
    ORTHOGONAL_ARRAY_SPECS,
    select_orthogonal_array,
)
from combinatorial_test_table_generator.orthogonal_array_validator import (
    parse_orthogonal_array,
    validate_orthogonal_array,
)


def request_for(level_counts, mode="auto"):
    return validate_request(
        {
            "mode": mode,
            "factors": [
                {
                    "name": f"因子{factor_index}",
                    "levels": [f"水平{index}" for index in range(level_count)],
                }
                for factor_index, level_count in enumerate(level_counts)
            ],
        }
    )


class OrthogonalArrayTests(unittest.TestCase):
    def test_parser_preserves_matrix_and_ignores_trailing_note(self):
        matrix = parse_orthogonal_array(
            "000\n011\n101\n110\nSource note.\n", expected_rows=4
        )

        self.assertEqual(matrix[-1], (1, 1, 0))
        self.assertEqual(len(matrix), 4)

    def test_validator_accepts_oa_4_3_2_2(self):
        matrix = parse_orthogonal_array("000\n011\n101\n110\n")

        result = validate_orthogonal_array(
            matrix, expected_rows=4, expected_columns=3, levels=2
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.pair_frequency, 1)

    def test_validator_rejects_unbalanced_matrix(self):
        matrix = parse_orthogonal_array("000\n000\n101\n110\n")

        result = validate_orthogonal_array(
            matrix, expected_rows=4, expected_columns=3, levels=2
        )

        self.assertFalse(result.passed)
        self.assertTrue(any("不满足严格均衡" in error for error in result.errors))

    def test_catalog_contains_ten_locally_verified_arrays(self):
        catalog_path = resources.files("reference_data").joinpath(
            "orthogonal_arrays", "catalog.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

        self.assertEqual(len(catalog["arrays"]), 10)
        self.assertTrue(all(item["validation"]["passed"] for item in catalog["arrays"]))

    def test_all_selection_ranges_choose_expected_array(self):
        factor_counts = (3, 7, 8, 4, 7, 8, 5, 8, 6, 8)
        for spec, factor_count in zip(ORTHOGONAL_ARRAY_SPECS, factor_counts):
            with self.subTest(array_id=spec.array_id):
                factors = tuple(
                    Factor(
                        f"F{factor_index}",
                        tuple(str(level) for level in range(spec.levels)),
                    )
                    for factor_index in range(factor_count)
                )
                selection, reason = select_orthogonal_array(factors)
                self.assertIsNone(reason)
                self.assertIsNotNone(selection)
                self.assertEqual(selection.spec.array_id, spec.array_id)

    def test_all_v02_ranges_generate_strict_arrays(self):
        factor_counts = (3, 7, 8, 4, 7, 8, 5, 8, 6, 8)
        for spec, factor_count in zip(ORTHOGONAL_ARRAY_SPECS, factor_counts):
            with self.subTest(array_id=spec.array_id):
                result = generate(request_for([spec.levels] * factor_count))
                self.assertEqual(result.method, "strict_orthogonal_array")
                self.assertEqual(result.orthogonal_array["array_id"], spec.array_id)
                self.assertEqual(result.coverage.coverage_rate, 1.0)

    def test_auto_prefers_strict_orthogonal_array(self):
        result = generate(request_for([2, 2, 2]))

        self.assertEqual(result.method, "strict_orthogonal_array")
        self.assertEqual(result.case_count, 4)
        self.assertEqual(result.orthogonal_array["array_id"], "OA(4,3,2,2)")
        self.assertEqual(result.coverage.coverage_rate, 1.0)

    def test_auto_falls_back_for_mixed_levels(self):
        result = generate(request_for([2, 3, 4]))

        self.assertEqual(result.method, "pairwise_covering_array")
        self.assertIsNone(result.orthogonal_array)
        self.assertIn("水平数不一致", result.warnings[0])
        self.assertEqual(result.coverage.coverage_rate, 1.0)

    def test_orthogonal_mode_reports_no_match(self):
        with self.assertRaisesRegex(InputValidationError, "水平数不一致"):
            generate(request_for([2, 3], mode="orthogonal"))

    def test_pairwise_mode_never_labels_result_as_orthogonal(self):
        result = generate(request_for([2, 2, 2], mode="pairwise"))

        self.assertEqual(result.method, "pairwise_covering_array")
        self.assertIsNone(result.orthogonal_array)


if __name__ == "__main__":
    unittest.main()
