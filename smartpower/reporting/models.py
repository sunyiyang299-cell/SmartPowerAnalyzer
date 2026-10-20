"""Immutable report metadata and original-order samples."""

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from smartpower.analysis.service import DatasetAnalysis
from smartpower.anomaly.models import DetectionResult, Thresholds
from smartpower.data.validation import DataError

DEFAULT_TITLE = "电力系统运行数据分析报告"
NOT_DETECTED = "本次未执行异常检测。"
NO_EVENTS = "未检测到符合当前阈值条件的异常记录。"
LIMITATIONS = (
    "导入文件仅表示来源未核验；模拟来源是用户可编辑标记，不具备防篡改证明能力。",
    "采用单相正弦稳态功率模型，电压和电流均为有效值；不适用于三相或谐波功率分解。",
    "无功功率仅计算绝对值 |Q|，不推断感性、容性、超前或滞后。",
    "功率因数平均值为各采样点算术平均，不是整个时间段的综合功率因数。",
    "全部采样点等权统计；非等间隔采样不进行时间加权，不计算电能。",
    "异常阈值为用户配置条件，不是国家标准限值；报告不属于设备安全认证报告。",
    "本报告不能代替专业计量仪器校准。",
    "如使用模拟来源：模拟数据，非真实设备测量，不能作为真实测量证据；本数据集来源见概况。",
)


def validate_title(title):
    if (not isinstance(title, str) or not title.strip() or len(title) > 120
            or any(ord(c) < 32 for c in title)):
        raise DataError("报告标题必须为 1～120 个字符，不能包含控制字符。")
    return title.strip()


@dataclass(frozen=True)
class ReportSnapshot:
    report_id: str
    product_name: str
    version: str
    title: str
    created_at: datetime
    analysis: DatasetAnalysis
    power_factors: np.ndarray
    thresholds: Thresholds | None
    detection: DetectionResult | None

    @property
    def source_label(self):
        return "模拟数据，非真实设备测量" if self.analysis.simulated else self.analysis.source

    @property
    def time_start(self):
        return np.min(self.analysis.times)

    @property
    def time_end(self):
        return np.max(self.analysis.times)

    @property
    def detection_status(self):
        if self.detection is None:
            return NOT_DETECTED
        return NO_EVENTS if not self.detection.events else "已执行用户阈值检测。"


def statistics_rows(snapshot):
    """One presentation mapping shared by PDF and XLSX; no new calculation."""
    a = snapshot.analysis
    rows = []
    for stats in (a.voltage, a.current, a.power.active_statistics, a.power.apparent_statistics,
                  a.power.reactive_abs_statistics, a.power.power_factor_statistics):
        for name, value in (("算术平均值", stats.mean), ("最大值", stats.maximum), ("最小值", stats.minimum)):
            rows.append((stats.quantity, name, value, stats.unit))
        if stats in (a.voltage, a.current, a.power.power_factor_statistics):
            rows.append((stats.quantity, "总体标准差（ddof=0）", stats.population_std, stats.unit))
    return rows
