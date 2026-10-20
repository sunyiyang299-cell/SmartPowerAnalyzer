import sqlite3

import numpy as np
import pandas as pd
import pytest

from smartpower.anomaly.detector import detect_anomalies
from smartpower.anomaly.models import Thresholds
from smartpower.anomaly.service import detect_saved_dataset
from smartpower.data.demo import generate_demo
from smartpower.data.validation import DataError
from smartpower.storage.repository import DatasetRepository


def sample(u, i=None):
    dataset = generate_demo(len(u))
    dataset.frame["电压"] = u
    dataset.frame["电流"] = i if i is not None else [10] * len(u)
    return dataset


def test_voltage_strict_boundaries_and_counts():
    result = detect_anomalies(sample([205, 210, 220, 230, 235]), Thresholds(210, 230, 20), 7)
    assert [(e.row_index, e.kind, e.value, e.threshold) for e in result.events] == [
        (0, "电压偏低", 205, 210), (4, "电压偏高", 235, 230)]
    assert result.type_counts == {"电压偏低": 1, "电压偏高": 1, "电流偏高": 0}
    assert result.unique_sample_count == 2
    assert all(e.dataset_id == 7 and "模拟数据" in e.source and e.unit == "V" for e in result.events)


def test_current_strict_boundaries():
    result = detect_anomalies(sample([220] * 4, [10, 20, 21, 30]), Thresholds(210, 230, 20))
    assert [(e.row_index, e.value) for e in result.events] == [(2, 21), (3, 30)]


def test_simultaneous_events_preserve_original_order_time_and_frame():
    dataset = sample([235, 205, 220], [30, 20, 10])
    dataset.frame["时间"] = pd.to_datetime(["2026-01-03", "2026-01-01", "2026-01-03"])
    dataset.frame.index = [91, 72, 33]  # Stored ordinal position, not arbitrary Pandas label.
    original = dataset.frame.copy(deep=True)
    result = detect_anomalies(dataset, Thresholds(210, 230, 20), 3)
    assert len(result.events) == 3 and result.unique_sample_count == 2
    assert [e.row_index for e in result.events] == [0, 0, 1]
    assert result.events[0].timestamp == np.datetime64("2026-01-03")
    pd.testing.assert_frame_equal(dataset.frame, original)


@pytest.mark.parametrize("values", [(-1, 230, 20), (230, 210, 20), (210, 210, 20), (210, 230, 0),
    (210, 230, -1), (float("nan"), 230, 20), (210, float("inf"), 20), (210, 230, float("inf")),
    ("210", 230, 20), (True, 230, 20), (210, 230, complex(20, 0))])
def test_invalid_thresholds(values):
    with pytest.raises(DataError):
        Thresholds(*values)


@pytest.mark.parametrize("column,value", [("电压", np.nan), ("电压", np.inf), ("电流", -1),
    ("电流", np.inf), ("功率因数", 1.2), ("电压", "不是数字"), ("时间", "错误时间")])
def test_invalid_dataset_is_rejected(column, value):
    dataset = sample([220])
    dataset.frame[column] = value
    with pytest.raises(DataError):
        detect_anomalies(dataset, Thresholds(210, 230, 20))


def test_empty_dataset():
    dataset = generate_demo(1)
    dataset.frame = dataset.frame.iloc[:0]
    with pytest.raises(DataError, match="没有数据"):
        detect_anomalies(dataset, Thresholds(210, 230, 20))


def test_wrong_dataset_type_is_explicit():
    with pytest.raises(DataError, match="数据集对象"):
        detect_anomalies(None, Thresholds(210, 230, 20))


def test_float_adjacent_boundaries_and_extremes():
    dataset = sample([np.nextafter(210., 0), 210, np.nextafter(230., np.inf), np.finfo(float).max, 0])
    result = detect_anomalies(dataset, Thresholds(210, 230, 20))
    assert [e.row_index for e in result.events] == [0, 2, 3, 4]


def test_database_and_simulated_provenance_unchanged(tmp_path):
    repo = DatasetRepository(tmp_path / "检测.sqlite3")
    identifier = repo.save(generate_demo(), "模拟数据")
    with sqlite3.connect(repo.path) as db:
        before = db.execute("SELECT * FROM samples ORDER BY position").fetchall()
        schema = db.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
    result = detect_saved_dataset(repo, identifier, Thresholds(210, 230, 20))
    assert result.count == 1000 and result.simulated and "模拟数据" in result.source
    assert all(e.source == result.source and e.dataset_id == identifier for e in result.events)
    with sqlite3.connect(repo.path) as db:
        assert db.execute("SELECT * FROM samples ORDER BY position").fetchall() == before
        assert db.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == schema
