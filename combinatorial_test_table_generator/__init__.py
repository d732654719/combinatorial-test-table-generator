"""组合测试表生成器。"""

from .models import CoverageReport, Factor, GenerationRequest, GenerationResult
from .pairwise_covering_generator import generate_pairwise

__all__ = [
    "CoverageReport",
    "Factor",
    "GenerationRequest",
    "GenerationResult",
    "generate_pairwise",
]

__version__ = "0.1.0"
