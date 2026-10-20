import numpy as np
import pandas as pd
import pytest

from smartpower.data.importer import import_file
from smartpower.data.validation import DataError, ValidationError, validate_frame


@pytest.fixture
def valid_frame():
    return pd.DataFrame({"时间": ["2026-10-20 10:00:00", "2026-10-20 10:00:01"],
                         "电压": [220, 221.5], "电流": [0, 10.5], "功率因数": [0, 1]})


@pytest.mark.parametrize("suffix", [".csv", ".xlsx"])
def test_normal_import_chinese_path(tmp_path, valid_frame, suffix):
    path = tmp_path / ("中文采样数据" + suffix)
    if suffix == ".csv":
        valid_frame.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        valid_frame.to_excel(path, index=False)
    dataset = import_file(path)
    assert dataset.name == "中文采样数据"
    assert len(dataset.frame) == 2
    assert dataset.frame["电压"].tolist() == [220, 221.5]
    assert dataset.frame["功率因数"].tolist() == [0, 1]
    assert pd.api.types.is_datetime64_any_dtype(dataset.frame["时间"])
    assert not dataset.simulated


@pytest.mark.parametrize("content", ["", "   \n", "时间,电压,电流,功率因数\n"])
def test_empty_file(tmp_path, content):
    path = tmp_path / "空.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DataError, match="空|没有数据"):
        import_file(path)


def test_missing_columns(valid_frame):
    with pytest.raises(DataError, match="缺少必需字段：电流"):
        validate_frame(valid_frame.drop(columns="电流"))


@pytest.mark.parametrize("column,value,reason", [
    ("时间", "2026-02-30", "无效时间"), ("时间", 1790000000, "无效时间"),
    ("时间", "2026-10-20T10:00:00Z", "无效时间"),
    ("电压", "abc", "合法数值"), ("电流", np.inf, "合法数值"),
    ("电流", True, "合法数值"), ("电压", -1, "不得为负"),
    ("电流", -0.01, "不得为负"), ("功率因数", 1.01, "0～1"),
    ("功率因数", -0.1, "0～1"), ("电压", None, "缺失值"),
    ("时间", "", "缺失值"), ("功率因数", "NaN", "合法数值"),
])
def test_invalid_values_report_row_and_column(valid_frame, column, value, reason):
    raw = valid_frame.astype(object)
    raw.loc[1, column] = value
    with pytest.raises(ValidationError, match=reason) as error:
        validate_frame(raw)
    assert error.value.issues[0].row == 2
    assert error.value.issues[0].column == column


def test_error_detail_is_bounded(valid_frame):
    raw = pd.concat([valid_frame] * 100, ignore_index=True).astype(object)
    raw["电压"] = "错误"
    with pytest.raises(ValidationError) as error:
        validate_frame(raw)
    assert error.value.count == 200
    assert len(error.value.issues) == 40


def test_bad_file_and_encoding(tmp_path, valid_frame):
    path = tmp_path / "国标编码.csv"
    valid_frame.to_csv(path, index=False, encoding="gb18030")
    assert len(import_file(path).frame) == 2
    path = tmp_path / "损坏.xlsx"
    path.write_bytes(b"not an excel archive")
    with pytest.raises(DataError, match="无法读取"):
        import_file(path)
    with pytest.raises(DataError, match="无法读取"):
        import_file(tmp_path / "不存在.csv")
    with pytest.raises(DataError, match="仅支持"):
        import_file(tmp_path / "文件.xls")


def test_whitespace_headers_extra_columns_and_duplicate_headers(valid_frame, tmp_path):
    raw = valid_frame.rename(columns={"时间": " 时间 "})
    raw["备注"] = "不保存"
    path = tmp_path / "扩展.csv"
    raw.to_csv(path, index=False)
    dataset = import_file(path)
    assert "备注" in dataset.warning
    assert list(dataset.frame.columns) == ["时间", "电压", "电流", "功率因数"]
    raw.columns = ["时间", " 电流 ", "电流", "功率因数", "备注"]
    with pytest.raises(DataError, match="重复"):
        validate_frame(raw)


@pytest.mark.parametrize("suffix", [".csv", ".xlsx"])
def test_duplicate_file_headers_are_not_silently_renamed(tmp_path, valid_frame, suffix):
    raw = valid_frame.copy()
    raw.columns = ["时间", "电流", "电流", "功率因数"]
    path = tmp_path / ("重复字段" + suffix)
    if suffix == ".csv":
        raw.to_csv(path, index=False)
    else:
        raw.to_excel(path, index=False)
    with pytest.raises(DataError, match="重复"):
        import_file(path)


def test_excel_datetime_cells_and_missing_numeric_cell(tmp_path, valid_frame):
    valid_frame["时间"] = pd.to_datetime(valid_frame["时间"])
    path = tmp_path / "日期单元格.xlsx"
    valid_frame.to_excel(path, index=False)
    assert len(import_file(path).frame) == 2
    raw = valid_frame.astype(object)
    raw.loc[0, "电流"] = None
    raw.to_excel(path, index=False)
    with pytest.raises(ValidationError, match="缺失值") as exc:
        import_file(path)
    assert exc.value.issues[0].row == 1


def test_import_simulation_marker_is_conservative(tmp_path, valid_frame):
    valid_frame["数据来源"] = ["模拟数据", "设备信息未验证"]
    path = tmp_path / "混合来源.csv"
    valid_frame.to_csv(path, index=False)
    assert import_file(path).simulated
