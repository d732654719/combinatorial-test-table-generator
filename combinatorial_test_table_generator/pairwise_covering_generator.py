"""确定性的两两覆盖表生成器。"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Iterable

from .models import Factor, GenerationRequest, GenerationResult
from .pairwise_coverage_validator import verify_pairwise_coverage

Interaction = tuple[int, int, int, int]
IndexRow = tuple[int, ...]


def _all_interactions(factors: tuple[Factor, ...]) -> set[Interaction]:
    interactions: set[Interaction] = set()
    for first_index, second_index in combinations(range(len(factors)), 2):
        for first_level in range(len(factors[first_index].levels)):
            for second_level in range(len(factors[second_index].levels)):
                interactions.add(
                    (first_index, first_level, second_index, second_level)
                )
    return interactions


def _row_interactions(row: IndexRow) -> tuple[Interaction, ...]:
    return tuple(
        (first_index, row[first_index], second_index, row[second_index])
        for first_index, second_index in combinations(range(len(row)), 2)
    )


def _complete_row(
    seed: Interaction,
    factors: tuple[Factor, ...],
    uncovered: set[Interaction],
) -> IndexRow:
    """从一个未覆盖组合出发，以确定性贪心策略补全一行。"""

    first_index, first_level, second_index, second_level = seed
    row: list[int | None] = [None] * len(factors)
    row[first_index] = first_level
    row[second_index] = second_level
    assigned = [first_index, second_index]

    for factor_index in range(len(factors)):
        if row[factor_index] is not None:
            continue

        best_level = 0
        best_gain = -1
        for candidate_level in range(len(factors[factor_index].levels)):
            gain = 0
            for assigned_index in assigned:
                assigned_level = row[assigned_index]
                assert assigned_level is not None
                if assigned_index < factor_index:
                    interaction = (
                        assigned_index,
                        assigned_level,
                        factor_index,
                        candidate_level,
                    )
                else:
                    interaction = (
                        factor_index,
                        candidate_level,
                        assigned_index,
                        assigned_level,
                    )
                gain += interaction in uncovered
            if gain > best_gain:
                best_gain = gain
                best_level = candidate_level

        row[factor_index] = best_level
        assigned.append(factor_index)

    return tuple(level for level in row if level is not None)


def _remove_redundant_rows(rows: Iterable[IndexRow]) -> list[IndexRow]:
    """删除移除后仍不影响覆盖率的行。"""

    kept_rows = list(rows)
    occurrence_count: Counter[Interaction] = Counter()
    for row in kept_rows:
        occurrence_count.update(_row_interactions(row))

    for row_index in range(len(kept_rows) - 1, -1, -1):
        interactions = _row_interactions(kept_rows[row_index])
        if all(occurrence_count[interaction] > 1 for interaction in interactions):
            for interaction in interactions:
                occurrence_count[interaction] -= 1
            del kept_rows[row_index]

    return kept_rows


def _generate_index_rows(factors: tuple[Factor, ...]) -> list[IndexRow]:
    uncovered = _all_interactions(factors)
    rows: list[IndexRow] = []

    while uncovered:
        seed = min(uncovered)
        row = _complete_row(seed, factors, uncovered)
        rows.append(row)
        uncovered.difference_update(_row_interactions(row))

    return _remove_redundant_rows(rows)


def generate_pairwise(request: GenerationRequest) -> GenerationResult:
    """生成并自行验证两两覆盖表。"""

    if request.mode != "pairwise" or request.strength != 2:
        raise ValueError("generate_pairwise 只接受 strength=2 的 pairwise 请求。")

    index_rows = _generate_index_rows(request.factors)
    coverage = verify_pairwise_coverage(index_rows, request.factors)
    if coverage.coverage_rate != 1.0:
        raise RuntimeError("生成器内部错误：生成结果未达到 100% 两两覆盖率。")

    cases: list[dict[str, str]] = []
    for case_number, row in enumerate(index_rows, start=1):
        case = {"case_id": f"case_{case_number:03d}"}
        case.update(
            {
                factor.name: factor.levels[row[factor_index]]
                for factor_index, factor in enumerate(request.factors)
            }
        )
        cases.append(case)

    return GenerationResult(
        method="pairwise_covering_array",
        coverage=coverage,
        test_cases=tuple(cases),
    )
