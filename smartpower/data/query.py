"""Vectorized view-index computation, called by background jobs."""

import numpy as np

from smartpower.data.importer import Dataset
from smartpower.data.validation import REQUIRED_COLUMNS


def query_rows(dataset: Dataset, text: str = "", column: str = "全部字段",
               sort_column: int = 0, ascending: bool = True) -> np.ndarray:
    frame = dataset.frame
    if text.strip():
        columns = list(REQUIRED_COLUMNS) if column == "全部字段" else [column]
        mask = np.zeros(len(frame), dtype=bool)
        for name in columns:
            mask |= frame[name].astype(str).str.contains(text.strip(), case=False, regex=False).to_numpy()
        frame = frame.loc[mask]
    if 0 <= sort_column < len(REQUIRED_COLUMNS):
        frame = frame.sort_values(REQUIRED_COLUMNS[sort_column], ascending=ascending, kind="stable")
    return frame.index.to_numpy(dtype=np.int64)
