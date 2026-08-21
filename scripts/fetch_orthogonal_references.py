"""手动下载、验证并登记 Sloane 严格正交表参考数据。"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from combinatorial_test_table_generator.orthogonal_array_selector import (  # noqa: E402
    ORTHOGONAL_ARRAY_SPECS,
)
from combinatorial_test_table_generator.orthogonal_array_validator import (  # noqa: E402
    parse_orthogonal_array,
    validate_orthogonal_array,
)

DESTINATION = PROJECT_ROOT / "reference_data" / "orthogonal_arrays"


def _download(url: str, attempts: int = 3) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "combinatorial-test-table-generator/0.2"},
    )
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt)
    assert last_error is not None
    raise last_error


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    catalog_entries: list[dict[str, object]] = []
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="oa-download-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        for spec in ORTHOGONAL_ARRAY_SPECS:
            try:
                raw_bytes = _download(spec.source_url)
                matrix = parse_orthogonal_array(
                    raw_bytes.decode("ascii"), expected_rows=spec.rows
                )
                validation = validate_orthogonal_array(
                    matrix,
                    expected_rows=spec.rows,
                    expected_columns=spec.columns,
                    levels=spec.levels,
                    strength=spec.strength,
                )
                if not validation.passed:
                    raise ValueError("；".join(validation.errors))

                temporary_file = temporary_root / spec.filename
                temporary_file.write_bytes(raw_bytes)
                destination_file = DESTINATION / spec.filename
                shutil.copyfile(temporary_file, destination_file)

                catalog_entries.append(
                    {
                        "array_id": spec.array_id,
                        "source_url": spec.source_url,
                        "download_date": date.today().isoformat(),
                        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                        "rows": spec.rows,
                        "columns": spec.columns,
                        "levels": spec.levels,
                        "strength": spec.strength,
                        "local_file": spec.filename,
                        "validation": validation.to_dict(),
                    }
                )
                print(f"通过：{spec.array_id} -> {spec.filename}")
            except (UnicodeDecodeError, ValueError, OSError) as exc:
                failures.append(f"{spec.array_id}：{exc}")
                print(f"失败：{spec.array_id}：{exc}", file=sys.stderr)

    catalog = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_library": "Sloane Orthogonal Array Library",
        "source_homepage": "https://neilsloane.com/oadir/",
        "arrays": catalog_entries,
    }
    catalog_path = DESTINATION / "catalog.json"
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="",
    )
    print(f"目录：{catalog_path}（{len(catalog_entries)} 张可用表）")

    if failures:
        print("以下表未进入可用目录：", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
