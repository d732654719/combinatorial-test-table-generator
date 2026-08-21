"""严格正交表解析与本地验证。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Sequence


@dataclass(frozen=True)
class OrthogonalValidationResult:
    """严格正交性验证结果。"""

    passed: bool
    errors: tuple[str, ...]
    pair_frequency: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": list(self.errors),
            "pair_frequency": self.pair_frequency,
        }


def parse_orthogonal_array(
    text: str, *, expected_rows: int | None = None
) -> tuple[tuple[int, ...], ...]:
    """解析 Sloane OA 矩阵区，兼容文件末尾的来源说明文字。"""

    matrix: list[tuple[int, ...]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if expected_rows is not None and len(matrix) == expected_rows:
            break
        line = raw_line.strip()
        if not line:
            continue
        tokens = line.split() if any(character.isspace() for character in line) else list(line)
        try:
            row = tuple(int(token) for token in tokens)
        except ValueError as exc:
            raise ValueError(f"第 {line_number} 行包含非整数值。") from exc
        matrix.append(row)

    if not matrix:
        raise ValueError("正交表文件没有数据行。")
    return tuple(matrix)


def validate_orthogonal_array(
    matrix: Sequence[Sequence[int]],
    *,
    expected_rows: int,
    expected_columns: int,
    levels: int,
    strength: int = 2,
) -> OrthogonalValidationResult:
    """验证矩阵尺寸、符号范围以及任意两列的严格均衡性。"""

    errors: list[str] = []
    if strength != 2:
        errors.append("当前验证器仅支持强度 2。")
    if len(matrix) != expected_rows:
        errors.append(f"应有 {expected_rows} 行，实际为 {len(matrix)} 行。")

    for row_number, row in enumerate(matrix, start=1):
        if len(row) != expected_columns:
            errors.append(
                f"第 {row_number} 行应有 {expected_columns} 列，实际为 {len(row)} 列。"
            )
            continue
        invalid_values = sorted({value for value in row if not 0 <= value < levels})
        if invalid_values:
            errors.append(
                f"第 {row_number} 行包含超出 0～{levels - 1} 的值：{invalid_values}。"
            )

    pair_frequency: int | None = None
    divisor = levels**2
    if expected_rows % divisor != 0:
        errors.append(f"行数 {expected_rows} 不能被水平组合数 {divisor} 整除。")
    else:
        pair_frequency = expected_rows // divisor

    dimensions_valid = (
        len(matrix) == expected_rows
        and all(len(row) == expected_columns for row in matrix)
        and all(0 <= value < levels for row in matrix for value in row)
    )
    if dimensions_valid and pair_frequency is not None and strength == 2:
        expected_pairs = {
            (first_level, second_level)
            for first_level in range(levels)
            for second_level in range(levels)
        }
        for first_column, second_column in combinations(range(expected_columns), 2):
            counts = Counter(
                (row[first_column], row[second_column]) for row in matrix
            )
            if set(counts) != expected_pairs or any(
                counts[pair] != pair_frequency for pair in expected_pairs
            ):
                errors.append(
                    f"第 {first_column + 1}、{second_column + 1} 列不满足严格均衡。"
                )

    return OrthogonalValidationResult(
        passed=not errors,
        errors=tuple(errors),
        pair_frequency=pair_frequency,
    )
