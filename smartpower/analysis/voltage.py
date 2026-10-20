"""Voltage RMS statistics, in volts."""

from smartpower.analysis.statistics import Statistics, summarize


def analyze_voltage(samples) -> Statistics:
    return summarize(samples, "电压有效值", "V")
