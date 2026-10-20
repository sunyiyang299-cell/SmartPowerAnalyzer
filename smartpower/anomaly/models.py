"""Immutable threshold configuration and auditable anomaly events."""

from dataclasses import dataclass
from numbers import Real
import math

from smartpower.data.validation import DataError

KINDS = ("电压偏低", "电压偏高", "电流偏高")
DISCLAIMER = "异常检测结果仅供数据分析参考，不构成设备安全或电气标准符合性认证。"


@dataclass(frozen=True)
class Thresholds:
    voltage_lower: float
    voltage_upper: float
    current_upper: float

    def __post_init__(self):
        for name, value in (("电压下限", self.voltage_lower), ("电压上限", self.voltage_upper),
                            ("电流上限", self.current_upper)):
            if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value < 0:
                raise DataError(f"{name}必须是非负有限数值，不允许 NaN 或 Infinity。")
        if self.voltage_lower >= self.voltage_upper:
            raise DataError("电压下限必须小于电压上限。")
        if self.current_upper <= 0:
            raise DataError("电流上限必须大于 0。")


@dataclass(frozen=True)
class AnomalyEvent:
    dataset_id: int | None
    row_index: int  # Zero-based original stored position; never time-sorted position.
    timestamp: object
    parameter: str
    value: float
    kind: str
    threshold: float
    unit: str
    source: str


@dataclass(frozen=True)
class DetectionResult:
    dataset_id: int | None
    dataset_name: str
    source: str
    simulated: bool
    count: int
    fingerprint: str
    thresholds: Thresholds
    events: tuple[AnomalyEvent, ...]
    unique_sample_count: int

    @property
    def type_counts(self):
        return {kind: sum(event.kind == kind for event in self.events) for kind in KINDS}
