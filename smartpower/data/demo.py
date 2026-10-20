"""Clearly identified demo data, never equipment measurements."""

import os
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from smartpower.data.importer import Dataset
from smartpower.data.validation import DataError, SIMULATED_SOURCE, SOURCE_COLUMN, validate_frame


def generate_demo(count: int = 1000, seed: int | None = 42) -> Dataset:
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise DataError("模拟数据条数必须为正整数。")
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({
        "时间": pd.date_range("2026-01-01 00:00:00", periods=count, freq="s"),
        "电压": rng.uniform(218, 242, count).round(3),
        "电流": rng.uniform(0.5, 25, count).round(3),
        "功率因数": rng.uniform(0.85, 1, count).round(4),
    })
    return Dataset("单相交流演示（模拟数据）", validate_frame(frame), simulated=True)


def export_demo(dataset: Dataset, path: str | Path) -> None:
    """Atomic replacement prevents a failed export from truncating an old file."""
    if not dataset.simulated:
        raise DataError("此入口仅允许导出明确标记的模拟数据。")
    path = Path(path)
    frame = validate_frame(dataset.frame)
    frame[SOURCE_COLUMN] = SIMULATED_SOURCE
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
        frame.to_csv(temporary, index=False, encoding="utf-8-sig")
        os.replace(temporary, path)
    except OSError as exc:
        raise DataError(f"导出失败：{exc}。原目标文件未被替换，请检查路径、权限或磁盘空间。") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    import argparse
    import sys
    # Redirected output on English Windows can default to cp1252. Use UTF-8
    # explicitly so a successful export never fails while printing its result.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="生成 1000 条模拟单相交流数据，非真实设备测量。")
    parser.add_argument("--output", type=Path, default=Path("模拟数据.csv"), help="输出 CSV 路径")
    parser.add_argument("--overwrite", action="store_true", help="明确允许覆盖已有文件")
    args = parser.parse_args()
    if args.output.exists() and not args.overwrite:
        parser.error("目标文件已存在。如需覆盖，请明确添加 --overwrite。")
    try:
        export_demo(generate_demo(), args.output)
    except DataError as exc:
        parser.error(str(exc))
    print(f"已导出 1000 条模拟数据（非真实设备测量）：{args.output}")


if __name__ == "__main__":
    main()
