from smartpower.data.demo import generate_demo
from smartpower.data.query import query_rows


def test_numeric_sort_and_literal_filter():
    data = generate_demo(10)
    data.frame.loc[:2, "电流"] = [100, 2, 11]
    ascending = query_rows(data, sort_column=2)
    assert data.frame.loc[ascending, "电流"].is_monotonic_increasing
    descending = query_rows(data, sort_column=2, ascending=False)
    assert data.frame.loc[descending, "电流"].is_monotonic_decreasing
    assert len(query_rows(data, "2026-01-01", "时间")) == 10
    assert len(query_rows(data, "[", "全部字段")) == 0
    assert data.frame.loc[0, "电流"] == 100
