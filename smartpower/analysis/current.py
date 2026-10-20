"""Current RMS sample maximum is NOT an instantaneous AC peak."""

from smartpower.analysis.statistics import Statistics, summarize


def analyze_current(samples) -> Statistics:
    return summarize(samples, "电流有效值", "A")
