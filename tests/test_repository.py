import sqlite3

import pandas as pd
import pytest

from smartpower.data.importer import Dataset
from smartpower.data.validation import DataError
from smartpower.storage.database import initialize_database
from smartpower.storage.repository import DatasetRepository, StorageError


@pytest.fixture
def dataset():
    return Dataset("模拟数据", pd.DataFrame({
        "时间": pd.to_datetime(["2026-10-20 10:00:00.123456789", "2026-10-20 10:00:01"], format="mixed"),
        "电压": [220.5, 0], "电流": [10.25, 0], "功率因数": [1, 0],
    }), simulated=True)


def test_store_list_reload_preserves_values_and_source(tmp_path, dataset):
    path = tmp_path / "中文目录" / "运行数据.sqlite3"
    repository = DatasetRepository(path)
    identifier = repository.save(dataset, " 名称 '带引号' ")
    history = DatasetRepository(path).list_datasets()
    assert history[0]["id"] == identifier
    assert history[0]["name"] == "名称 '带引号'"
    assert history[0]["imported_at"]
    assert history[0]["row_count"] == 2
    loaded = repository.load(identifier)
    pd.testing.assert_frame_equal(loaded.frame, dataset.frame.astype({"电流": float, "功率因数": float}))
    assert loaded.simulated


def test_delete_only_requested_dataset_and_cascade(tmp_path, dataset):
    repo = DatasetRepository(tmp_path / "data.sqlite3")
    first = repo.save(dataset, "第一个")
    second = repo.save(dataset, "第二个")
    repo.delete(first)
    assert [row["id"] for row in repo.list_datasets()] == [second]
    assert len(repo.load(second).frame) == 2
    with sqlite3.connect(repo.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM samples WHERE dataset_id=?", (first,)).fetchone()[0] == 0
    with pytest.raises(StorageError, match="不存在"):
        repo.load(first)
    with pytest.raises(StorageError, match="不存在"):
        repo.delete(first)


def test_invalid_input_never_saved(tmp_path, dataset):
    repo = DatasetRepository(tmp_path / "data.sqlite3")
    with pytest.raises(DataError, match="名称"):
        repo.save(dataset, " ")
    dataset.frame.loc[0, "功率因数"] = 2
    with pytest.raises(DataError, match="0～1"):
        repo.save(dataset, "错误")
    assert repo.list_datasets() == []


def test_transaction_rolls_back_partial_insert(tmp_path, dataset):
    repo = DatasetRepository(tmp_path / "data.sqlite3")
    existing = repo.save(dataset, "已有")
    with sqlite3.connect(repo.path) as connection:
        connection.execute("CREATE TRIGGER reject_second BEFORE INSERT ON samples WHEN NEW.position=1 "
                           "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    with pytest.raises(StorageError, match="回滚"):
        repo.save(dataset, "应回滚")
    assert [r["id"] for r in repo.list_datasets()] == [existing]
    assert len(repo.load(existing).frame) == 2


def test_database_failure_and_v01_migration(tmp_path, dataset):
    path = tmp_path / "legacy.sqlite3"
    initialize_database(path)
    repo = DatasetRepository(path)
    assert repo.list_datasets() == []
    repo.save(dataset, "迁移后保存")
    assert len(repo.list_datasets()) == 1
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT value FROM app_metadata WHERE key='schema_version'").fetchone()[0] == "2"
    with pytest.raises(StorageError, match="数据库操作失败"):
        DatasetRepository(tmp_path).list_datasets()


def test_newer_schema_is_not_overwritten(tmp_path):
    path = tmp_path / "future.sqlite3"
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE app_metadata SET value='99'")
    with pytest.raises(StorageError, match="版本不受支持"):
        DatasetRepository(path).list_datasets()
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT value FROM app_metadata").fetchone()[0] == "99"


def test_failed_delete_keeps_dataset_and_samples(tmp_path, dataset):
    repo = DatasetRepository(tmp_path / "data.sqlite3")
    identifier = repo.save(dataset, "保留")
    with sqlite3.connect(repo.path) as connection:
        connection.execute("CREATE TRIGGER reject_delete BEFORE DELETE ON samples "
                           "BEGIN SELECT RAISE(ABORT, 'injected deletion failure'); END")
    with pytest.raises(StorageError, match="回滚"):
        repo.delete(identifier)
    assert repo.list_datasets()[0]["id"] == identifier
    assert len(repo.load(identifier).frame) == 2
