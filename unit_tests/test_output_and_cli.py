import csv
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from combinatorial_test_table_generator.command_line_interface import build_parser, main
from combinatorial_test_table_generator.generator import generate
from combinatorial_test_table_generator.input_schema import validate_request
from combinatorial_test_table_generator.output_formatters import (
    format_csv,
    format_json,
    format_markdown,
)
from combinatorial_test_table_generator.pairwise_covering_generator import (
    generate_pairwise,
)


def generated_result():
    request = validate_request(
        {
            "mode": "pairwise",
            "factors": [
                {"name": "界面", "levels": ["列表", "详情"]},
                {"name": "权限", "levels": ["管理员", "访客"]},
            ],
        }
    )
    return generate_pairwise(request)


class OutputAndCliTests(unittest.TestCase):
    def test_json_output_contains_metadata_and_cases(self):
        data = json.loads(format_json(generated_result()))

        self.assertEqual(data["method"], "pairwise_covering_array")
        self.assertEqual(data["coverage"]["coverage_rate"], 1.0)
        self.assertIsNone(data["orthogonal_array"])
        self.assertEqual(data["case_count"], len(data["test_cases"]))

    def test_markdown_output_has_case_id_as_first_column(self):
        output = format_markdown(generated_result())

        self.assertIn("| case_id | 界面 | 权限 |", output)
        self.assertIn("两两覆盖率：100.00%", output)

    def test_csv_output_has_one_row_per_case(self):
        result = generated_result()
        rows = list(csv.DictReader(io.StringIO(format_csv(result))))

        self.assertEqual(len(rows), result.case_count)
        self.assertEqual(list(rows[0]), ["case_id", "界面", "权限"])

    def test_cli_writes_requested_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.json"
            output_path = Path(temp_dir) / "cases.csv"
            input_path.write_text(
                json.dumps(
                    {
                        "factors": [
                            {"name": "A", "levels": ["0", "1"]},
                            {"name": "B", "levels": ["0", "1", "2"]},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "--input",
                    str(input_path),
                    "--format",
                    "csv",
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            with output_path.open(encoding="utf-8", newline="") as output_file:
                self.assertEqual(len(list(csv.DictReader(output_file))), 6)

    def test_cli_accepts_short_mode_values_and_flags(self):
        parser = build_parser()

        self.assertEqual(parser.parse_args(["--mode", "o"]).mode, "o")
        self.assertEqual(parser.parse_args(["-p"]).mode_flag, "pairwise")
        self.assertEqual(parser.parse_args(["-a"]).mode_flag, "auto")

    def test_cli_defaults_need_no_arguments(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            (temporary_root / "factors.json").write_text(
                json.dumps(
                    {
                        "factors": [
                            {"name": "A", "levels": ["0", "1"]},
                            {"name": "B", "levels": ["0", "1"]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            original_directory = Path.cwd()
            try:
                os.chdir(temporary_root)
                exit_code = main([])
            finally:
                os.chdir(original_directory)

            self.assertEqual(exit_code, 0)
            output = (temporary_root / "case_table.md").read_text(encoding="utf-8")
            self.assertIn("严格正交表：`OA(4,3,2,2)`", output)

    def test_markdown_includes_orthogonal_source(self):
        request = validate_request(
            {
                "mode": "auto",
                "factors": [
                    {"name": "A", "levels": ["0", "1"]},
                    {"name": "B", "levels": ["0", "1"]},
                ],
            }
        )

        output = format_markdown(generate(request))

        self.assertIn("严格正交表：`OA(4,3,2,2)`", output)
        self.assertIn("https://neilsloane.com/oadir/oa.4.3.2.2.txt", output)

    def test_cli_returns_chinese_error_for_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.json"
            input_path.write_text("{", encoding="utf-8")
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(["--input", str(input_path)])

            self.assertEqual(exit_code, 2)
            self.assertIn("错误：输入文件不是有效的 JSON", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
