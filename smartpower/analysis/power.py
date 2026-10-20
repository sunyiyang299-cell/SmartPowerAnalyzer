"""Single-phase sinusoidal steady-state power from nonnegative RMS inputs."""

from dataclasses import dataclass

import numpy as np

from smartpower.analysis.power_factor import analyze_power_factor
from smartpower.analysis.statistics import AnalysisError, Statistics, numeric_samples, summarize

POWER_MODEL = "仅适用于单相正弦稳态交流：U、I 为有效值，PF 为 0～1 的非负功率因数。"
POWER_LIMITATION = "无功功率仅为绝对值，不能判定感性/容性或超前/滞后；不适用于三相或非正弦谐波分析。"


@dataclass(frozen=True)
class PowerAnalysis:
    active: np.ndarray
    apparent: np.ndarray
    reactive_abs: np.ndarray
    active_statistics: Statistics
    apparent_statistics: Statistics
    reactive_abs_statistics: Statistics
    power_factor_statistics: Statistics


def analyze_power(voltage, current, power_factor) -> PowerAnalysis:
    u = numeric_samples(voltage, "电压有效值")
    i = numeric_samples(current, "电流有效值")
    pf = numeric_samples(power_factor, "功率因数", upper=1.0)
    if not (len(u) == len(i) == len(pf)):
        raise AnalysisError("电压、电流与功率因数采样数量必须一致，不能广播计算。")
    try:
        with np.errstate(over="raise", invalid="raise", under="ignore"):
            apparent = u * i
            active = apparent * pf
            # (1-pf)*(1+pf) is algebraically 1-pf**2, with less
            # cancellation near unity. Invalid PF is rejected before this.
            reactive = apparent * np.sqrt(np.maximum(0.0, (1.0 - pf) * (1.0 + pf)))
    except FloatingPointError as exc:
        raise AnalysisError("功率结果超出 float64 可表示范围，请检查单位与输入数量级。") from exc
    if not all(np.isfinite(a).all() for a in (active, apparent, reactive)):
        raise AnalysisError("功率结果包含非有限值，已拒绝本次计算。")
    # A positive physical result rounded down to zero is unrepresentable,
    # not a zero-load measurement. Exact zeros (U/I=0, PF=0 or PF=1) remain valid.
    if (np.any((u > 0) & (i > 0) & (apparent == 0))
            or np.any((apparent > 0) & (pf > 0) & (active == 0))
            or np.any((apparent > 0) & (pf < 1) & (reactive == 0))):
        raise AnalysisError("非零功率结果小于 float64 可表示范围，已拒绝将其当作零值输出。")
    active_stats = summarize(active, "有功功率", "W")
    apparent_stats = summarize(apparent, "视在功率", "VA")
    reactive_stats = summarize(reactive, "无功功率绝对值 |Q|", "var")
    pf_stats = analyze_power_factor(pf)
    for array in (active, apparent, reactive):
        array.setflags(write=False)
    return PowerAnalysis(active, apparent, reactive, active_stats, apparent_stats, reactive_stats, pf_stats)
