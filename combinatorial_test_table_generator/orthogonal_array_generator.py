"""将严格正交表映射为用户测试 Case。"""

from __future__ import annotations

from .models import GenerationRequest, GenerationResult
from .orthogonal_array_selector import SelectedOrthogonalArray
from .orthogonal_array_validator import validate_orthogonal_array
from .pairwise_coverage_validator import verify_pairwise_coverage


def generate_orthogonal(
    request: GenerationRequest, selection: SelectedOrthogonalArray
) -> GenerationResult:
    """投影所需列、映射水平名称并再次验证结果。"""

    factor_count = len(request.factors)
    index_rows = tuple(tuple(row[:factor_count]) for row in selection.matrix)
    projected_validation = validate_orthogonal_array(
        index_rows,
        expected_rows=selection.spec.rows,
        expected_columns=factor_count,
        levels=selection.spec.levels,
        strength=2,
    )
    if not projected_validation.passed:
        raise RuntimeError(
            "严格正交表列投影验证失败：" + "；".join(projected_validation.errors)
        )

    coverage = verify_pairwise_coverage(index_rows, request.factors)
    if coverage.coverage_rate != 1.0:
        raise RuntimeError("严格正交表映射后未达到 100% 两两覆盖率。")

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

    spec = selection.spec
    return GenerationResult(
        method="strict_orthogonal_array",
        coverage=coverage,
        test_cases=tuple(cases),
        orthogonal_array={
            "array_id": spec.array_id,
            "rows": spec.rows,
            "columns": spec.columns,
            "selected_columns": factor_count,
            "levels": spec.levels,
            "strength": spec.strength,
            "source_url": spec.source_url,
            "local_file": spec.filename,
            "sha256": selection.catalog_entry["sha256"],
            "validation_passed": True,
        },
    )
