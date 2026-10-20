"""Arithmetic sample PF statistics, not an interval aggregate power factor."""

from smartpower.analysis.statistics import Statistics, summarize


def analyze_power_factor(samples) -> Statistics:
    return summarize(samples, "功率因数（采样点）", "无量纲", upper=1.0)
