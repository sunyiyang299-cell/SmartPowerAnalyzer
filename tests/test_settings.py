from dataclasses import replace
import json

import pytest

from smartpower.data.validation import DataError
from smartpower.settings.manager import SettingsManager


@pytest.fixture
def manager(tmp_path):
    return SettingsManager(tmp_path / "用户配置" / "settings.json", tmp_path)


def test_defaults_read_without_creating_directory(manager, tmp_path):
    loaded = manager.load()
    assert not loaded.warning
    assert loaded.value.report_directory == str(tmp_path.resolve())
    assert loaded.value.chart_directory == str(tmp_path.resolve())
    assert loaded.value.startup_page == "home"
    assert not manager.path.parent.exists()


def test_save_and_new_manager_reload(manager, tmp_path):
    value = replace(manager.defaults, report_title="专业运行报告", startup_page="reports")
    manager.save(value)
    other = SettingsManager(manager.path, tmp_path)
    assert other.load().value == value
    assert json.loads(manager.path.read_text(encoding="utf-8"))["version"] == 1


@pytest.mark.parametrize("payload", ["{坏了", "[]", '{"version":99,"settings":{}}',
    '{"version":1,"settings":{"report_directory": false}}', "x" * 65537],
    ids=["broken-json", "wrong-root", "future-version", "wrong-fields", "oversized"])
def test_corrupt_config_safe_fallback_and_original_preserved(manager, payload):
    manager.path.parent.mkdir()
    manager.path.write_text(payload, encoding="utf-8")
    loaded = manager.load()
    assert loaded.value == manager.defaults and "原文件保留" in loaded.warning
    assert manager.path.read_text(encoding="utf-8") == payload


@pytest.mark.parametrize("field,value", [("report_directory", "relative/path"), ("chart_directory", "不存在目录"),
    ("report_title", ""), ("report_title", "x" * 121), ("startup_page", "bad"), ("font_path", "不存在.ttf")])
def test_invalid_preferences_do_not_create_or_overwrite(manager, field, value):
    manager.save(manager.defaults)
    before = manager.path.read_bytes()
    with pytest.raises(DataError):
        manager.save(replace(manager.defaults, **{field: value}))
    assert manager.path.read_bytes() == before


def test_nonexistent_absolute_export_directory_never_created(manager, tmp_path):
    target = tmp_path / "不应创建"
    with pytest.raises(DataError, match="未自动创建"):
        manager.save(replace(manager.defaults, report_directory=str(target)))
    assert not target.exists()


def test_failed_atomic_save_preserves_old(manager, monkeypatch):
    manager.save(manager.defaults)
    before = manager.path.read_bytes()
    def fail(*args):
        raise OSError("测试写入失败")
    monkeypatch.setattr("smartpower.settings.manager.os.replace", fail)
    with pytest.raises(DataError, match="旧设置文件保留"):
        manager.save(replace(manager.defaults, report_title="新标题"))
    assert manager.path.read_bytes() == before
    assert list(manager.path.parent.iterdir()) == [manager.path]
