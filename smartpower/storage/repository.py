"""Transactional dataset repository. No Qt or GUI state in this module."""

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3

import pandas as pd

from smartpower.data.importer import Dataset
from smartpower.data.validation import DataError, validate_frame


class StorageError(DataError):
    """Storage errors translated for the UI without hiding the original cause."""


class DatasetRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @contextmanager
    def _connection(self):
        connection = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path, timeout=5)
            connection.execute("PRAGMA foreign_keys=ON")
            with connection:
                connection.execute("CREATE TABLE IF NOT EXISTS app_metadata "
                                   "(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                row = connection.execute("SELECT value FROM app_metadata WHERE key='schema_version'").fetchone()
                if row and row[0] not in ("1", "2"):
                    raise StorageError("数据库版本不受支持，请使用相应版本的软件，原数据未修改。")
                connection.execute("""CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(trim(name))>0),
                    imported_at TEXT NOT NULL, simulated INTEGER NOT NULL CHECK(simulated IN (0,1)),
                    row_count INTEGER NOT NULL CHECK(row_count>0))""")
                connection.execute("""CREATE TABLE IF NOT EXISTS samples (
                    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                    position INTEGER NOT NULL, sampled_at TEXT NOT NULL,
                    voltage REAL NOT NULL CHECK(voltage>=0), current REAL NOT NULL CHECK(current>=0),
                    power_factor REAL NOT NULL CHECK(power_factor>=0 AND power_factor<=1),
                    PRIMARY KEY(dataset_id, position))""")
                connection.execute("INSERT INTO app_metadata VALUES ('schema_version','2') "
                                   "ON CONFLICT(key) DO UPDATE SET value='2'")
            yield connection
        except StorageError:
            raise
        except (sqlite3.Error, OSError) as exc:
            raise StorageError(f"数据库操作失败：{exc}。本次写入已回滚，当前预览仍可重新保存；请检查路径、权限或磁盘空间。") from exc
        finally:
            if connection is not None:
                connection.close()

    def save(self, dataset: Dataset, name: str) -> int:
        name = name.strip()
        if not name or len(name) > 200:
            raise DataError("数据集名称不能为空，且不能超过 200 个字符。")
        frame = validate_frame(dataset.frame)
        with self._connection() as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO datasets(name,imported_at,simulated,row_count) VALUES (?,?,?,?)",
                    (name, datetime.now().astimezone().isoformat(timespec="seconds"),
                     int(dataset.simulated), len(frame)),
                )
                dataset_id = cursor.lastrowid
                connection.executemany(
                    "INSERT INTO samples VALUES (?,?,?,?,?,?)",
                    ((dataset_id, pos, time.isoformat(), float(voltage), float(current), float(pf))
                     for pos, (time, voltage, current, pf) in
                     enumerate(frame.itertuples(index=False, name=None))),
                )
        return int(dataset_id)

    def list_datasets(self) -> list[dict]:
        with self._connection() as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(
                "SELECT * FROM datasets ORDER BY id DESC")]

    def load(self, dataset_id: int) -> Dataset:
        with self._connection() as connection:
            with connection:
                connection.execute("BEGIN")
                row = connection.execute("SELECT name,simulated,row_count FROM datasets WHERE id=?",
                                         (dataset_id,)).fetchone()
                if row is None:
                    raise StorageError("指定数据集不存在，可能已被删除，请刷新历史列表。")
                records = connection.execute(
                    "SELECT sampled_at,voltage,current,power_factor FROM samples "
                    "WHERE dataset_id=? ORDER BY position", (dataset_id,)).fetchall()
                if len(records) != row[2]:
                    raise StorageError("数据集记录数与元数据不一致，已停止读取，请保留数据库并检查。")
        try:
            frame = validate_frame(pd.DataFrame(records, columns=["时间", "电压", "电流", "功率因数"]))
        except DataError as exc:
            raise StorageError(f"历史数据校验失败：{exc}") from exc
        return Dataset(row[0], frame, bool(row[1]))

    def delete(self, dataset_id: int) -> None:
        """Caller must obtain user confirmation before invoking this method."""
        with self._connection() as connection:
            with connection:
                cursor = connection.execute("DELETE FROM datasets WHERE id=?", (dataset_id,))
                if cursor.rowcount != 1:
                    raise StorageError("数据集不存在或已删除，请刷新历史列表。")
