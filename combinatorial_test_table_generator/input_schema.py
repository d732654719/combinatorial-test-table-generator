"""JSON 输入读取与 v0.1 规则校验。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Factor, GenerationRequest


class InputValidationError(ValueError):
    """输入不符合项目规格。"""


def load_request(path: str | Path, mode_override: str | None = None) -> GenerationRequest:
    """读取 UTF-8 JSON 文件并返回已校验的请求。"""

    input_path = Path(path)
    try:
        raw_text = input_path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise InputValidationError(f"输入文件不存在：{input_path}") from exc
    except OSError as exc:
        raise InputValidationError(f"无法读取输入文件：{exc}") from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InputValidationError(
            f"输入文件不是有效的 JSON（第 {exc.lineno} 行，第 {exc.colno} 列）：{exc.msg}"
        ) from exc

    return validate_request(data, mode_override=mode_override)


def validate_request(data: Any, mode_override: str | None = None) -> GenerationRequest:
    """按 v0.1 支持范围校验一个已解析的 JSON 值。"""

    if not isinstance(data, dict):
        raise InputValidationError("JSON 顶层必须是对象。")

    mode = mode_override if mode_override is not None else data.get("mode", "pairwise")
    if mode not in {"auto", "orthogonal", "pairwise"}:
        raise InputValidationError("mode 必须是 auto、orthogonal 或 pairwise。")
    if mode != "pairwise":
        raise InputValidationError(
            f"v0.1 仅支持 pairwise 模式；{mode} 模式将在 v0.2 提供。"
        )

    strength = data.get("strength", 2)
    if isinstance(strength, bool) or not isinstance(strength, int) or strength != 2:
        raise InputValidationError("v0.1 的 strength 仅支持整数 2。")

    raw_factors = data.get("factors")
    if not isinstance(raw_factors, list):
        raise InputValidationError("factors 必须是数组。")
    if not 2 <= len(raw_factors) <= 8:
        raise InputValidationError("v0.1 要求 factors 包含 2～8 个因子。")

    factors: list[Factor] = []
    seen_names: set[str] = set()
    for factor_index, raw_factor in enumerate(raw_factors, start=1):
        prefix = f"第 {factor_index} 个因子"
        if not isinstance(raw_factor, dict):
            raise InputValidationError(f"{prefix}必须是对象。")

        name = raw_factor.get("name")
        if not isinstance(name, str) or not name.strip():
            raise InputValidationError(f"{prefix}的 name 必须是非空字符串。")
        if name != name.strip():
            raise InputValidationError(f"{prefix}的 name 不能以空白字符开头或结尾。")
        if name == "case_id":
            raise InputValidationError("因子名称不能使用保留字段 case_id。")
        if name in seen_names:
            raise InputValidationError(f"因子名称不能重复：{name}")
        seen_names.add(name)

        raw_levels = raw_factor.get("levels")
        if not isinstance(raw_levels, list):
            raise InputValidationError(f"因子“{name}”的 levels 必须是数组。")
        if not 2 <= len(raw_levels) <= 10:
            raise InputValidationError(f"因子“{name}”必须包含 2～10 个水平。")

        levels: list[str] = []
        seen_levels: set[str] = set()
        for level_index, level in enumerate(raw_levels, start=1):
            if not isinstance(level, str) or not level.strip():
                raise InputValidationError(
                    f"因子“{name}”的第 {level_index} 个水平必须是非空字符串。"
                )
            if level != level.strip():
                raise InputValidationError(
                    f"因子“{name}”的水平不能以空白字符开头或结尾：{level!r}"
                )
            if level in seen_levels:
                raise InputValidationError(f"因子“{name}”的水平不能重复：{level}")
            seen_levels.add(level)
            levels.append(level)

        factors.append(Factor(name=name, levels=tuple(levels)))

    return GenerationRequest(mode=mode, strength=strength, factors=tuple(factors))
