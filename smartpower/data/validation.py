"""Single-phase RMS schema. Reject a batch rather than silently drop rows."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("时间", "电压", "电流", "功率因数")
SOURCE_COLUMN = "数据来源"
SIMULATED_SOURCE = "模拟数据（非真实设备测量）"
IMPORTED_SOURCE = "导入文件（来源未核验）"


class DataError(ValueError):
    """Actionable user-facing data error."""


@dataclass(frozen=True)
class Issue:
    row: int
    column: str
    reason: str


class ValidationError(DataError):
    def __init__(self, issues: list[Issue], count: int):
        self.issues = issues
        self.count = count
        detail = "\n".join(f"数据第 {i.row} 行 · {i.column}：{i.reason}" for i in issues)
        super().__init__(f"校验失败，共 {count} 处错误（数据行从表头下一行开始计数）。\n{detail}"
                         + ("\n仅展示前 40 处，请修正文件后重新导入。" if count > len(issues) else ""))


def validate_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """Return a normalized copy, never mutate the input or invent values.

    Times are local calendar strings or Excel datetime cells, without timezone.
    Numeric epoch/Excel serial timestamps are rejected to avoid guessing units.
    Extra columns are handled explicitly by the importer.
    """
    if raw.empty:
        raise DataError("文件没有数据记录，请检查是否为空文件或只有表头。")
    frame = raw.copy(deep=False)
    columns = [str(c).strip().lstrip("\ufeff") for c in frame.columns]
    if len(columns) != len(set(columns)):
        raise DataError("存在重复字段名称，请为每一列使用唯一的表头。")
    frame = frame.set_axis(columns, axis=1)
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise DataError("缺少必需字段：" + "、".join(missing))
    result = pd.DataFrame(index=range(len(frame)))
    issues: list[Issue] = []
    count = 0

    def record(mask, column, reason):
        nonlocal count
        positions = np.flatnonzero(np.asarray(mask, dtype=bool))
        count += len(positions)
        for pos in positions[:max(0, 40 - len(issues))]:
            issues.append(Issue(int(pos) + 1, column, reason))

    for column in REQUIRED_COLUMNS:
        series = frame[column].reset_index(drop=True)
        text = series.astype("string").str.strip()
        missing_mask = series.isna() | text.eq("").fillna(False)
        record(missing_mask, column, "缺失值")
        if column == "时间":
            calendar = text.str.match(
                r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[ T]\d{1,2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?)?$"
            ).fillna(False)
            values = pd.to_datetime(text.where(calendar).str.replace("/", "-"),
                                    format="mixed", errors="coerce")
            record(~missing_mask & values.isna(), column,
                   "无效时间，请使用年-月-日 时:分:秒；不接受数字时间戳或时区")
        else:
            # Strings exclude booleans and complex values as well as nonnumeric text.
            values = pd.to_numeric(text, errors="coerce").astype(float)
            invalid = ~np.isfinite(values.to_numpy())
            record(~missing_mask & invalid, column, "必须为有限的合法数值")
            if column == "功率因数":
                record(~missing_mask & ~invalid & ((values < 0) | (values > 1)),
                       column, "必须位于 0～1（含端点）")
            else:
                record(~missing_mask & ~invalid & (values < 0), column, "有效值不得为负数")
        result[column] = values
    if count:
        raise ValidationError(issues, count)
    return result
