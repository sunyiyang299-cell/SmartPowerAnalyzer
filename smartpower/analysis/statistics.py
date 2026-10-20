"""Validated float64 statistics with population (ddof=0) deviation."""

from dataclasses import dataclass

import numpy as np

from smartpower.data.validation import DataError


class AnalysisError(DataError):
    """Invalid analysis input or an unrepresentable numerical result."""


@dataclass(frozen=True)
class Statistics:
    quantity: str
    unit: str
    count: int
    mean: float
    maximum: float
    minimum: float
    population_std: float


def numeric_samples(values, quantity: str, upper: float | None = None) -> np.ndarray:
    """Accept one-dimensional real numeric samples; never coerce text/bools."""
    try:
        raw = np.asarray(values)
        if raw.ndim != 1:
            raise AnalysisError(f"{quantity}必须是一维数值序列。")
        if raw.size == 0:
            raise AnalysisError(f"{quantity}数据集为空，无法计算。")
        if raw.dtype.kind not in "iuf" or (
            isinstance(values, (list, tuple)) and any(isinstance(v, (bool, np.bool_)) for v in values)
        ):
            raise AnalysisError(f"{quantity}类型错误：仅接受实数，不接受文本、布尔值或复数。")
        with np.errstate(over="raise", invalid="raise"):
            samples = raw.astype(np.float64, copy=True)
    except AnalysisError:
        raise
    except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
        raise AnalysisError(f"{quantity}数据类型或数值范围无效。") from exc
    if not np.isfinite(samples).all():
        raise AnalysisError(f"{quantity}含 NaN 或 Infinity，无法计算。")
    if np.any(samples < 0):
        raise AnalysisError(f"{quantity}不得为负数。")
    if upper is not None and np.any(samples > upper):
        raise AnalysisError(f"{quantity}必须位于 0～{upper:g}（含端点）。")
    return samples


def summarize(values, quantity: str, unit: str, upper: float | None = None) -> Statistics:
    samples = numeric_samples(values, quantity, upper)
    maximum = float(np.max(samples))
    minimum = float(np.min(samples))
    # Scaling keeps both the sum in mean and the squared deviations in std
    # finite for very large, otherwise valid nonnegative float64 samples.
    if maximum == 0:
        mean = deviation = 0.0
    else:
        with np.errstate(over="raise", invalid="raise", under="ignore"):
            normalized = samples / maximum
            mean = float(np.mean(normalized, dtype=np.float64) * maximum)
            deviation = float(np.std(normalized, dtype=np.float64, ddof=0) * maximum)
    if not np.isfinite([mean, deviation]).all():
        raise AnalysisError(f"{quantity}统计结果超出 float64 数值范围。")
    return Statistics(quantity, unit, int(samples.size), mean, maximum, minimum, deviation)
