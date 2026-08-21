"""JSON、Markdown 与 CSV 输出。"""

from __future__ import annotations

import csv
import io
import json

from .models import GenerationResult


def format_json(result: GenerationResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n"


def _escape_markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def format_markdown(result: GenerationResult) -> str:
    if not result.test_cases:
        return "# 组合测试 Case 表\n\n无测试 Case。\n"

    coverage_percent = result.coverage.coverage_rate * 100
    lines = [
        "# 组合测试 Case 表",
        "",
        f"- 生成方法：`{result.method}`",
        f"- Case 数：{result.case_count}",
        (
            f"- 两两覆盖率：{coverage_percent:.2f}% "
            f"（{result.coverage.covered_combinations}/"
            f"{result.coverage.required_combinations}）"
        ),
    ]
    if result.orthogonal_array:
        lines.extend(
            [
                f"- 严格正交表：`{result.orthogonal_array['array_id']}`",
                f"- 参考来源：{result.orthogonal_array['source_url']}",
            ]
        )
    lines.extend(f"- 提示：{warning}" for warning in result.warnings)
    lines.append("")
    headers = list(result.test_cases[0])
    lines.append("| " + " | ".join(_escape_markdown_cell(item) for item in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for case in result.test_cases:
        lines.append(
            "| "
            + " | ".join(_escape_markdown_cell(case[header]) for header in headers)
            + " |"
        )
    return "\n".join(lines) + "\n"


def format_csv(result: GenerationResult) -> str:
    if not result.test_cases:
        return ""
    output = io.StringIO(newline="")
    headers = list(result.test_cases[0])
    writer = csv.DictWriter(output, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(result.test_cases)
    return output.getvalue()


FORMATTERS = {
    "json": format_json,
    "markdown": format_markdown,
    "csv": format_csv,
}
