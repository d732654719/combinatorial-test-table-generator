import unittest

from combinatorial_test_table_generator.input_schema import (
    InputValidationError,
    validate_request,
)


def valid_input():
    return {
        "mode": "pairwise",
        "strength": 2,
        "factors": [
            {"name": "浏览器", "levels": ["Chrome", "Firefox"]},
            {"name": "网络", "levels": ["Wi-Fi", "5G"]},
        ],
    }


class InputSchemaTests(unittest.TestCase):
    def test_valid_input_is_normalized(self):
        request = validate_request(valid_input())

        self.assertEqual(request.mode, "pairwise")
        self.assertEqual(request.strength, 2)
        self.assertEqual(request.factors[0].levels, ("Chrome", "Firefox"))

    def test_mode_defaults_to_auto(self):
        data = valid_input()
        del data["mode"]

        self.assertEqual(validate_request(data).mode, "auto")

    def test_accepts_all_v02_modes(self):
        for mode in ("auto", "orthogonal", "pairwise"):
            with self.subTest(mode=mode):
                data = valid_input()
                data["mode"] = mode
                self.assertEqual(validate_request(data).mode, mode)

    def test_cli_mode_override_takes_precedence(self):
        data = valid_input()
        data["mode"] = "auto"

        request = validate_request(data, mode_override="pairwise")

        self.assertEqual(request.mode, "pairwise")

    def test_rejects_duplicate_factor_names(self):
        data = valid_input()
        data["factors"][1]["name"] = "浏览器"

        with self.assertRaisesRegex(InputValidationError, "因子名称不能重复"):
            validate_request(data)

    def test_rejects_duplicate_levels(self):
        data = valid_input()
        data["factors"][0]["levels"] = ["Chrome", "Chrome"]

        with self.assertRaisesRegex(InputValidationError, "水平不能重复"):
            validate_request(data)

    def test_rejects_out_of_scope_factor_count(self):
        data = valid_input()
        data["factors"] = data["factors"] * 5

        with self.assertRaisesRegex(InputValidationError, "2～8"):
            validate_request(data)

    def test_rejects_case_id_as_factor_name(self):
        data = valid_input()
        data["factors"][0]["name"] = "case_id"

        with self.assertRaisesRegex(InputValidationError, "保留字段"):
            validate_request(data)


if __name__ == "__main__":
    unittest.main()
