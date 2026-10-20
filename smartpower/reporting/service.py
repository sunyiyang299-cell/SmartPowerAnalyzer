"""Load exactly once, reuse V0.3/V0.4, and freeze buffers before rendering."""

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import numpy as np

from smartpower.analysis.service import analyze_dataset
from smartpower.anomaly.detector import detect_anomalies
from smartpower.config import APP_NAME, APP_VERSION
from smartpower.data.importer import Dataset
from smartpower.data.validation import validate_frame
from smartpower.data.validation import DataError
from smartpower.reporting.models import DEFAULT_TITLE, ReportSnapshot, validate_title


def frozen_array(values):
    values = np.asarray(values)
    # bytes-backed buffers cannot be made writable again by setflags.
    return np.frombuffer(values.tobytes(), dtype=values.dtype).reshape(values.shape)


def build_report_snapshot(repository, dataset_id, *, title=DEFAULT_TITLE, thresholds=None):
    title = validate_title(title)
    loaded = repository.load(dataset_id)
    if not isinstance(loaded.name, str) or any(ord(c) < 32 for c in loaded.name):
        raise DataError("数据集名称包含控制字符或类型无效，无法生成报告；请先更正名称。")
    dataset = Dataset(loaded.name, validate_frame(loaded.frame), loaded.simulated)
    analysis = analyze_dataset(dataset, "all", dataset_id)
    sample = analysis.samples
    sample = replace(sample, order=frozen_array(sample.order), seconds=frozen_array(sample.seconds),
                     voltage=frozen_array(sample.voltage), current=frozen_array(sample.current))
    power = replace(analysis.power, active=frozen_array(analysis.power.active),
                    apparent=frozen_array(analysis.power.apparent), reactive_abs=frozen_array(analysis.power.reactive_abs))
    analysis = replace(analysis, times=frozen_array(analysis.times), samples=sample, power=power)
    detection = detect_anomalies(dataset, thresholds, dataset_id) if thresholds is not None else None
    return ReportSnapshot(str(uuid4()), APP_NAME, APP_VERSION, title, datetime.now(timezone.utc), analysis,
                          frozen_array(dataset.frame["功率因数"].to_numpy()), thresholds, detection)
