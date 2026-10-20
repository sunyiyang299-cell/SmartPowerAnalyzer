"""Pandas file readers, independent of Qt and persistence."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from smartpower.data.validation import (
    DataError, IMPORTED_SOURCE, REQUIRED_COLUMNS, SIMULATED_SOURCE, SOURCE_COLUMN, validate_frame,
)


@dataclass
class Dataset:
    name: str
    frame: pd.DataFrame
    simulated: bool = False
    warning: str = ""

    @property
    def source(self) -> str:
        return SIMULATED_SOURCE if self.simulated else IMPORTED_SOURCE


def import_file(path: str | Path) -> Dataset:
    path = Path(path)
    if path.suffix.lower() not in (".csv", ".xlsx"):
        raise DataError("仅支持 .csv 和 .xlsx 文件。")
    try:
        if path.stat().st_size == 0:
            raise DataError("文件为空，请选择包含表头和数据的文件。")
        if path.suffix.lower() == ".csv":
            try:
                raw = pd.read_csv(path, encoding="utf-8-sig", dtype=object, header=None,
                                  keep_default_na=False, skip_blank_lines=False)
            except UnicodeDecodeError:
                raw = pd.read_csv(path, encoding="gb18030", dtype=object, header=None,
                                  keep_default_na=False, skip_blank_lines=False)
        else:
            raw = pd.read_excel(path, engine="openpyxl", sheet_name=0, header=None,
                                dtype=object, keep_default_na=False)
    except DataError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise DataError("文件为空或没有可识别的表头。") from exc
    except Exception as exc:
        raise DataError(f"无法读取文件“{path.name}”：{exc}。请检查文件格式、权限及是否损坏。") from exc
    if raw.empty:
        raise DataError("文件没有数据记录。")
    headers = raw.iloc[0].tolist()
    raw = raw.iloc[1:].reset_index(drop=True)
    raw.columns = headers
    frame = validate_frame(raw)
    raw.columns = [str(c).strip().lstrip("\ufeff") for c in raw.columns]
    simulated = SOURCE_COLUMN in raw and raw[SOURCE_COLUMN].astype(str).str.contains("模拟", regex=False).any()
    extra = [c for c in raw.columns if c not in (*REQUIRED_COLUMNS, SOURCE_COLUMN)]
    warning = ""
    if extra:
        warning = "以下额外字段不参与预览和保存：" + "、".join(extra)
    return Dataset(path.stem, frame, bool(simulated), warning)
