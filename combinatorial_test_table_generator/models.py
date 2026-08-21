"""核心数据模型。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Factor:
    """一个测试因子及其可选水平。"""

    name: str
    levels: tuple[str, ...]


@dataclass(frozen=True)
class GenerationRequest:
    """通过输入校验后的生成请求。"""

    mode: str
    strength: int
    factors: tuple[Factor, ...]


@dataclass(frozen=True)
class CoverageReport:
    """两两组合覆盖率报告。"""

    strength: int
    required_combinations: int
    covered_combinations: int
    coverage_rate: float
    uncovered_combinations: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strength": self.strength,
            "required_combinations": self.required_combinations,
            "covered_combinations": self.covered_combinations,
            "coverage_rate": self.coverage_rate,
            "uncovered_combinations": list(self.uncovered_combinations),
        }


@dataclass(frozen=True)
class GenerationResult:
    """可序列化的生成结果。"""

    method: str
    coverage: CoverageReport
    test_cases: tuple[dict[str, str], ...]
    warnings: tuple[str, ...] = ()
    orthogonal_array: dict[str, Any] | None = None

    @property
    def case_count(self) -> int:
        return len(self.test_cases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "case_count": self.case_count,
            "coverage": self.coverage.to_dict(),
            "orthogonal_array": self.orthogonal_array,
            "warnings": list(self.warnings),
            "test_cases": list(self.test_cases),
        }
