"""Reuse V0.2 Dataset, validation and repository without schema changes."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from smartpower.analysis.current import analyze_current
from smartpower.analysis.power import PowerAnalysis, analyze_power
from smartpower.analysis.statistics import AnalysisError, Statistics
from smartpower.analysis.voltage import analyze_voltage
from smartpower.data.importer import Dataset
from smartpower.data.validation import validate_frame
from smartpower.storage.repository import DatasetRepository
from smartpower.visualization.snapshot import PlotSamples, prepare_samples


@dataclass(frozen=True)
class DatasetAnalysis:
    dataset_id: int | None
    dataset_name: str
    source: str
    simulated: bool
    count: int
    times: np.ndarray
    voltage: Statistics | None
    current: Statistics | None
    power: PowerAnalysis | None
    samples: PlotSamples | None = None


def analyze_dataset(dataset: Dataset, mode: str = "all", dataset_id: int | None = None) -> DatasetAnalysis:
    if not isinstance(dataset, Dataset) or not isinstance(dataset.frame, pd.DataFrame):
        raise AnalysisError("分析输入必须是 V0.2 数据集对象及其数据表。")
    if mode not in ("all", "voltage", "current", "power"):
        raise AnalysisError("不支持的分析模块。")
    frame = validate_frame(dataset.frame)
    u = frame["电压"].to_numpy()
    i = frame["电流"].to_numpy()
    pf = frame["功率因数"].to_numpy()
    voltage = analyze_voltage(u) if mode in ("all", "voltage") else None
    current = analyze_current(i) if mode in ("all", "current") else None
    power = analyze_power(u, i, pf) if mode in ("all", "power") else None
    times = frame["时间"].to_numpy(copy=True)
    times.setflags(write=False)
    return DatasetAnalysis(dataset_id, dataset.name, dataset.source, dataset.simulated,
                           len(frame), times, voltage, current, power, prepare_samples(frame))


def analyze_saved_dataset(repository: DatasetRepository, dataset_id: int, mode: str = "all") -> DatasetAnalysis:
    return analyze_dataset(repository.load(dataset_id), mode, dataset_id)
