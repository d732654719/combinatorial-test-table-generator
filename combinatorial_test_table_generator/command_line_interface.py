"""命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .generator import generate
from .input_schema import InputValidationError, load_request
from .output_formatters import FORMATTERS

MODE_ALIASES = {
    "a": "auto",
    "auto": "auto",
    "o": "orthogonal",
    "orthogonal": "orthogonal",
    "p": "pairwise",
    "pairwise": "pairwise",
}

DEFAULT_OUTPUTS = {
    "json": "case_table.json",
    "markdown": "case_table.md",
    "csv": "case_table.csv",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="combinatorial-test-table-generator",
        description="根据 JSON 因子定义生成严格正交表或两两覆盖测试表。",
    )
    parser.add_argument(
        "--input",
        default="factors.json",
        help="UTF-8 JSON 输入文件（默认：factors.json）",
    )
    parser.add_argument(
        "--format",
        choices=tuple(FORMATTERS),
        default="markdown",
        help="输出格式（默认：markdown）",
    )
    parser.add_argument(
        "--output",
        help="输出文件（默认：case_table.对应扩展名；使用 - 写入标准输出）",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--mode",
        choices=tuple(MODE_ALIASES),
        help="生成模式：a/auto、o/orthogonal、p/pairwise（默认：auto）",
    )
    mode_group.add_argument("-a", dest="mode_flag", action="store_const", const="auto", help="auto 模式")
    mode_group.add_argument("-o", dest="mode_flag", action="store_const", const="orthogonal", help="严格正交表模式")
    mode_group.add_argument("-p", dest="mode_flag", action="store_const", const="pairwise", help="两两覆盖模式")
    parser.add_argument("--version", action="version", version="%(prog)s 0.3.0")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        mode_override = MODE_ALIASES.get(args.mode) if args.mode else args.mode_flag
        request = load_request(args.input, mode_override=mode_override)
        result = generate(request)
        content = FORMATTERS[args.format](result)

        output_name = args.output or DEFAULT_OUTPUTS[args.format]
        if output_name == "-":
            sys.stdout.write(content)
        else:
            output_path = Path(output_name)
            output_path.write_text(content, encoding="utf-8", newline="")
    except (InputValidationError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"内部错误：{exc}", file=sys.stderr)
        return 1
    return 0
