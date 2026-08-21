"""按模式调度严格正交表或两两覆盖生成。"""

from __future__ import annotations

from dataclasses import replace

from .input_schema import InputValidationError
from .models import GenerationRequest, GenerationResult
from .orthogonal_array_generator import generate_orthogonal
from .orthogonal_array_selector import select_orthogonal_array
from .pairwise_covering_generator import generate_pairwise


def generate(request: GenerationRequest) -> GenerationResult:
    """根据 pairwise、orthogonal 或 auto 模式生成测试表。"""

    if request.mode == "pairwise":
        return generate_pairwise(request)

    selection, reason = select_orthogonal_array(request.factors)
    if selection is not None:
        return generate_orthogonal(request, selection)

    if request.mode == "orthogonal":
        raise InputValidationError(f"无法生成严格正交表：{reason}")

    pairwise_request = replace(request, mode="pairwise")
    pairwise_result = generate_pairwise(pairwise_request)
    return replace(
        pairwise_result,
        warnings=(f"{reason}已生成两两覆盖表。",),
    )
