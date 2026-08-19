"""两两覆盖率的独立验证逻辑。"""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

from .models import CoverageReport, Factor

Interaction = tuple[int, int, int, int]


def _required_interactions(factors: tuple[Factor, ...]) -> set[Interaction]:
    return {
        (first_index, first_level, second_index, second_level)
        for first_index, second_index in combinations(range(len(factors)), 2)
        for first_level in range(len(factors[first_index].levels))
        for second_level in range(len(factors[second_index].levels))
    }


def verify_pairwise_coverage(
    rows: Iterable[Sequence[int]], factors: tuple[Factor, ...]
) -> CoverageReport:
    """验证索引矩阵并报告未覆盖的因子水平组合。"""

    required = _required_interactions(factors)
    covered: set[Interaction] = set()

    for row_number, row in enumerate(rows, start=1):
        if len(row) != len(factors):
            raise ValueError(f"第 {row_number} 行的列数与因子数不一致。")
        for factor_index, level_index in enumerate(row):
            if isinstance(level_index, bool) or not isinstance(level_index, int):
                raise ValueError(f"第 {row_number} 行包含非整数水平索引。")
            if not 0 <= level_index < len(factors[factor_index].levels):
                raise ValueError(f"第 {row_number} 行包含越界水平索引。")
        covered.update(
            (first_index, row[first_index], second_index, row[second_index])
            for first_index, second_index in combinations(range(len(factors)), 2)
        )

    uncovered = sorted(required - covered)
    uncovered_details = tuple(
        {
            factors[first_index].name: factors[first_index].levels[first_level],
            factors[second_index].name: factors[second_index].levels[second_level],
        }
        for first_index, first_level, second_index, second_level in uncovered
    )
    required_count = len(required)
    covered_count = required_count - len(uncovered)
    coverage_rate = covered_count / required_count if required_count else 1.0

    return CoverageReport(
        strength=2,
        required_combinations=required_count,
        covered_combinations=covered_count,
        coverage_rate=coverage_rate,
        uncovered_combinations=uncovered_details,
    )
