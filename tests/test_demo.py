import pandas as pd
import pytest

from smartpower.data.demo import export_demo, generate_demo
from smartpower.data.importer import import_file
from smartpower.data.validation import DataError, SIMULATED_SOURCE


def test_generate_1000_valid_reproducible_rows():
    demo = generate_demo()
    assert demo.simulated
    assert len(demo.frame) == 1000
    assert demo.frame["电压"].between(218, 242).all()
    assert demo.frame["电流"].between(0.5, 25).all()
    assert demo.frame["功率因数"].between(0.85, 1).all()
    assert demo.frame["时间"].is_monotonic_increasing
    pd.testing.assert_frame_equal(demo.frame, generate_demo().frame)


def test_export_csv_keeps_simulation_marker_on_reimport(tmp_path):
    path = tmp_path / "模拟数据.csv"
    demo = generate_demo()
    export_demo(demo, path)
    exported = pd.read_csv(path, encoding="utf-8-sig")
    assert exported["数据来源"].eq(SIMULATED_SOURCE).all()
    loaded = import_file(path)
    assert loaded.simulated
    pd.testing.assert_frame_equal(loaded.frame, demo.frame)


def test_export_failure_preserves_existing_file(tmp_path, monkeypatch):
    path = tmp_path / "原数据.csv"
    path.write_text("原内容", encoding="utf-8")
    def fail(*args):
        raise PermissionError("测试拒绝替换")
    monkeypatch.setattr("smartpower.data.demo.os.replace", fail)
    with pytest.raises(DataError, match="导出失败"):
        export_demo(generate_demo(), path, overwrite=True)
    assert path.read_text(encoding="utf-8") == "原内容"
    assert not list(tmp_path.glob("*.tmp"))


def test_demo_arguments_and_real_data_export_rejected(tmp_path):
    with pytest.raises(DataError):
        generate_demo(0)
    demo = generate_demo()
    demo.simulated = False
    with pytest.raises(DataError, match="仅允许"):
        export_demo(demo, tmp_path / "fake.csv")


def test_independent_generator_cli_and_overwrite_guard(tmp_path):
    from pathlib import Path
    import subprocess
    import sys
    import os
    path = tmp_path / "命令行模拟.csv"
    command = [sys.executable, "-m", "smartpower.data.demo", "--output", str(path)]
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "已导出" in result.stdout.decode("utf-8")
    assert len(import_file(path).frame) == 1000
    original = path.read_bytes()
    result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=30)
    assert result.returncode != 0
    assert path.read_bytes() == original
