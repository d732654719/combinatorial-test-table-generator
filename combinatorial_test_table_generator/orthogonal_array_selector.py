"""内置严格正交表目录、加载与选择。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib import resources
from typing import Any

from .models import Factor
from .orthogonal_array_validator import (
    parse_orthogonal_array,
    validate_orthogonal_array,
)


@dataclass(frozen=True)
class OrthogonalArraySpec:
    array_id: str
    rows: int
    columns: int
    levels: int
    strength: int
    filename: str
    source_url: str


@dataclass(frozen=True)
class SelectedOrthogonalArray:
    spec: OrthogonalArraySpec
    matrix: tuple[tuple[int, ...], ...]
    catalog_entry: dict[str, Any]


SLOANE_BASE_URL = "https://neilsloane.com/oadir"


def _spec(rows: int, columns: int, levels: int) -> OrthogonalArraySpec:
    filename = f"oa.{rows}.{columns}.{levels}.2.txt"
    return OrthogonalArraySpec(
        array_id=f"OA({rows},{columns},{levels},2)",
        rows=rows,
        columns=columns,
        levels=levels,
        strength=2,
        filename=filename,
        source_url=f"{SLOANE_BASE_URL}/{filename}",
    )


ORTHOGONAL_ARRAY_SPECS = (
    _spec(4, 3, 2),
    _spec(8, 7, 2),
    _spec(12, 11, 2),
    _spec(9, 4, 3),
    _spec(18, 7, 3),
    _spec(27, 13, 3),
    _spec(16, 5, 4),
    _spec(32, 9, 4),
    _spec(25, 6, 5),
    _spec(50, 11, 5),
)


def _matching_spec(factor_count: int, level_count: int) -> OrthogonalArraySpec | None:
    return next(
        (
            spec
            for spec in ORTHOGONAL_ARRAY_SPECS
            if spec.levels == level_count and factor_count <= spec.columns
        ),
        None,
    )


def _reference_directory():
    return resources.files("reference_data").joinpath("orthogonal_arrays")


def selection_requirement(factors: tuple[Factor, ...]) -> tuple[OrthogonalArraySpec | None, str | None]:
    """判断输入是否有可匹配的等水平 OA 规格。"""

    level_counts = {len(factor.levels) for factor in factors}
    if len(level_counts) != 1:
        return None, "当前因子水平数不一致，无法使用等水平严格正交表。"

    level_count = next(iter(level_counts))
    spec = _matching_spec(len(factors), level_count)
    if spec is None:
        return (
            None,
            f"没有匹配 {len(factors)} 个因子、每因子 {level_count} 个水平的内置严格正交表。",
        )
    return spec, None


def select_orthogonal_array(
    factors: tuple[Factor, ...],
) -> tuple[SelectedOrthogonalArray | None, str | None]:
    """选择并在运行时重新验证一份内置严格正交表。"""

    spec, reason = selection_requirement(factors)
    if spec is None:
        return None, reason

    reference_directory = _reference_directory()
    catalog_path = reference_directory.joinpath("catalog.json")
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return None, f"严格正交表目录不可用：{exc}"

    entry = next(
        (item for item in catalog.get("arrays", []) if item.get("array_id") == spec.array_id),
        None,
    )
    if not entry or not entry.get("validation", {}).get("passed"):
        return None, f"{spec.array_id} 没有通过目录中的本地验证。"

    data_path = reference_directory.joinpath(spec.filename)
    try:
        raw_bytes = data_path.read_bytes()
        actual_hash = hashlib.sha256(raw_bytes).hexdigest()
        if actual_hash != entry.get("sha256"):
            return None, f"{spec.array_id} 文件哈希与已验证目录不一致。"
        matrix = parse_orthogonal_array(
            raw_bytes.decode("ascii"), expected_rows=spec.rows
        )
    except (FileNotFoundError, UnicodeDecodeError, ValueError, OSError) as exc:
        return None, f"无法读取 {spec.array_id}：{exc}"

    validation = validate_orthogonal_array(
        matrix,
        expected_rows=spec.rows,
        expected_columns=spec.columns,
        levels=spec.levels,
        strength=spec.strength,
    )
    if not validation.passed:
        return None, f"{spec.array_id} 运行时验证失败：{'；'.join(validation.errors)}"

    return SelectedOrthogonalArray(spec, matrix, entry), None
