"""Strict comparisons on every validated original sample, without mutation."""

import numpy as np
import pandas as pd

from smartpower.anomaly.models import AnomalyEvent, DetectionResult, Thresholds
from smartpower.data.validation import DataError, validate_frame
from smartpower.data.importer import Dataset
from smartpower.visualization.snapshot import frame_fingerprint


def detect_anomalies(dataset, thresholds: Thresholds, dataset_id=None):
    if not isinstance(dataset, Dataset) or not isinstance(dataset.frame, pd.DataFrame):
        raise DataError("检测输入必须是 V0.2 数据集对象及其数据表。")
    if not isinstance(thresholds, Thresholds):
        raise DataError("请提供有效的用户阈值配置。")
    frame = validate_frame(dataset.frame)
    u, i = frame["电压"].to_numpy(), frame["电流"].to_numpy()
    times = frame["时间"].to_numpy()
    events = []
    for mask, parameter, values, kind, limit, unit in (
        (u < thresholds.voltage_lower, "电压", u, "电压偏低", thresholds.voltage_lower, "V"),
        (u > thresholds.voltage_upper, "电压", u, "电压偏高", thresholds.voltage_upper, "V"),
        (i > thresholds.current_upper, "电流", i, "电流偏高", thresholds.current_upper, "A"),
    ):
        events.extend(AnomalyEvent(dataset_id, int(row), times[row], parameter, float(values[row]),
                                   kind, float(limit), unit, dataset.source)
                      for row in np.flatnonzero(mask))
    events.sort(key=lambda event: (event.row_index, event.kind))
    return DetectionResult(dataset_id, dataset.name, dataset.source, dataset.simulated, len(frame),
                           frame_fingerprint(frame), thresholds, tuple(events),
                           len({event.row_index for event in events}))
