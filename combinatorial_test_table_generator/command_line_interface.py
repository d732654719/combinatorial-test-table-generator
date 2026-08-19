"""命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .input_schema import InputValidationError, load_request
from .output_formatters import FORMATTERS
from .pairwise_covering_generator import generate_pairwise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="combinatorial-test-table-generator",
        description="根据 JSON 因子定义生成确定性的两两覆盖测试表。",
    )
    parser.add_argument("--input", required=True, help="UTF-8 JSON 输入文件")
    parser.add_argument(
        "--format",
        choices=tuple(FORMATTERS),
        default="json",
        help="输出格式（默认：json）",
    )
    parser.add_argument("--output", help="输出文件；省略时写入标准输出")
    parser.add_argument(
        "--mode",
        choices=("pairwise", "auto", "orthogonal"),
        help="覆盖输入文件中的 mode；v0.1 仅支持 pairwise",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        request = load_request(args.input, mode_override=args.mode)
        result = generate_pairwise(request)
        content = FORMATTERS[args.format](result)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(content, encoding="utf-8", newline="")
        else:
            sys.stdout.write(content)
    except (InputValidationError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"内部错误：{exc}", file=sys.stderr)
        return 1
    return 0
