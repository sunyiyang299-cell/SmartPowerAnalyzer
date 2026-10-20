import sqlite3

import numpy as np
import pytest

from smartpower.analysis.service import analyze_dataset, analyze_saved_dataset
from smartpower.data.demo import generate_demo
from smartpower.data.validation import DataError, SIMULATED_SOURCE
from smartpower.storage.repository import DatasetRepository


def test_v02_saved_demo_full_analysis_preserves_source_and_schema(tmp_path):
    repository = DatasetRepository(tmp_path / "历史数据.sqlite3")
    dataset = generate_demo()
    identifier = repository.save(dataset, "V0.2 模拟数据")
    with sqlite3.connect(repository.path) as connection:
        schema_before = connection.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
    result = analyze_saved_dataset(repository, identifier)
    assert result.dataset_id == identifier
    assert result.dataset_name == "V0.2 模拟数据"
    assert result.simulated
    assert result.source == SIMULATED_SOURCE
    assert result.count == 1000
    assert result.voltage.mean == pytest.approx(np.mean(dataset.frame["电压"]))
    assert result.current.population_std == pytest.approx(np.std(dataset.frame["电流"], ddof=0))
    expected = dataset.frame["电压"] * dataset.frame["电流"] * dataset.frame["功率因数"]
    np.testing.assert_allclose(result.power.active, expected, rtol=1e-12)
    assert len(result.times) == 1000
    assert not result.times.flags.writeable
    with sqlite3.connect(repository.path) as connection:
        assert connection.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == schema_before
        assert connection.execute("SELECT value FROM app_metadata WHERE key='schema_version'").fetchone()[0] == "2"
    assert len(repository.load(identifier).frame) == 1000


def test_invalid_or_empty_dataset_is_rejected():
    dataset = generate_demo()
    dataset.frame = dataset.frame.iloc[:0]
    with pytest.raises(DataError, match="没有数据"):
        analyze_dataset(dataset)
    with pytest.raises(DataError, match="数据集对象"):
        analyze_dataset(None)
    with pytest.raises(DataError, match="不支持"):
        analyze_dataset(generate_demo(), mode="missing")


def test_voltage_analysis_does_not_depend_on_representability_of_power():
    dataset = generate_demo(1)
    dataset.simulated = False
    dataset.frame["电压"] = np.finfo(float).max
    dataset.frame["电流"] = 2.0
    result = analyze_dataset(dataset, mode="voltage")
    assert result.power is None
    assert result.voltage.maximum == np.finfo(float).max
    assert not result.simulated
    assert "未核验" in result.source
    with pytest.raises(DataError, match="可表示范围"):
        analyze_dataset(dataset, mode="power")


def test_deleted_dataset_and_corrupted_data_fail_explicitly(tmp_path):
    repository = DatasetRepository(tmp_path / "data.sqlite3")
    identifier = repository.save(generate_demo(2), "将删除")
    repository.delete(identifier)
    with pytest.raises(DataError, match="不存在"):
        analyze_saved_dataset(repository, identifier)
    dataset = generate_demo(2)
    dataset.frame.loc[0, "功率因数"] = 1.2
    with pytest.raises(DataError, match="0～1"):
        analyze_dataset(dataset)
