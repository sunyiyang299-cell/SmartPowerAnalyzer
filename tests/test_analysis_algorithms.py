from decimal import Decimal, localcontext
import math

import numpy as np
import pytest

from smartpower.analysis.current import analyze_current
from smartpower.analysis.power import analyze_power
from smartpower.analysis.power_factor import analyze_power_factor
from smartpower.analysis.statistics import AnalysisError
from smartpower.analysis.voltage import analyze_voltage


def test_known_single_phase_case_1():
    result = analyze_power([220], [10], [0.9])
    assert result.active[0] == pytest.approx(1980, rel=1e-12)
    assert result.apparent[0] == pytest.approx(2200, rel=1e-12)
    # Independent triangle formula: sqrt(2200**2 - 1980**2).
    # The request's 958.47 approximation is inconsistent with its formula.
    assert result.reactive_abs[0] == pytest.approx(math.sqrt(919600), rel=1e-12)
    assert result.reactive_abs[0] == pytest.approx(958.957767578948, rel=1e-12)
    assert result.active_statistics.unit == "W"
    assert result.apparent_statistics.unit == "VA"
    assert result.reactive_abs_statistics.unit == "var"


@pytest.mark.parametrize("u,i,pf,p,s,q", [
    (0, 10, 0.9, 0, 0, 0), (220, 0, 0.9, 0, 0, 0),
    (220, 10, 1, 2200, 2200, 0), (220, 10, 0, 0, 2200, 2200),
])
def test_zero_and_boundary_cases(u, i, pf, p, s, q):
    result = analyze_power([u], [i], [pf])
    np.testing.assert_allclose(result.active, [p], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(result.apparent, [s], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(result.reactive_abs, [q], rtol=1e-12, atol=1e-12)


def test_voltage_population_statistics():
    result = analyze_voltage([220, 221, 219])
    assert result.count == 3
    assert result.unit == "V"
    assert result.mean == pytest.approx(220, rel=1e-12)
    assert result.maximum == 221
    assert result.minimum == 219
    assert result.population_std == pytest.approx(math.sqrt(2 / 3), rel=1e-12)


def test_current_rms_statistics_and_single_sample():
    result = analyze_current([2, 10, 6])
    assert result.quantity == "电流有效值"
    assert result.maximum == 10  # RMS sample maximum, not sqrt(2)*10.
    assert result.mean == pytest.approx(6)
    assert result.population_std == pytest.approx(math.sqrt(32 / 3))
    assert result.unit == "A"
    assert analyze_current([5]).population_std == 0


def test_arithmetic_pf_statistics():
    result = analyze_power_factor([0.8, 0.9, 1])
    assert result.mean == pytest.approx(0.9)
    assert result.maximum == 1
    assert result.minimum == 0.8
    assert result.population_std == pytest.approx(math.sqrt(0.02 / 3))
    assert result.unit == "无量纲"


@pytest.mark.parametrize("values", [
    [], [np.nan], [np.inf], [-np.inf], [-1], ["220"], ["错误"],
    [True], [220, False], [1 + 0j], [None], None, 220, [[220, 221]],
])
@pytest.mark.parametrize("analyzer", [analyze_voltage, analyze_current, analyze_power_factor])
def test_bad_numeric_inputs_are_rejected(analyzer, values):
    with pytest.raises(AnalysisError):
        analyzer(values)


@pytest.mark.parametrize("u,i,pf", [
    ([], [], []), ([np.nan], [1], [0.9]), ([1], [np.inf], [0.9]),
    ([1], [1], [np.nan]), ([-1], [1], [0.9]), ([1], [-1], [0.9]),
    ([1], [1], [-0.1]), ([1], [1], [1.2]), ([1], [1], [np.nextafter(1.0, 2.0)]),
    ([1, 2], [1], [0.9, 0.9]), (["220"], [10], [0.9]),
])
def test_bad_power_inputs_are_rejected(u, i, pf):
    with pytest.raises(AnalysisError):
        analyze_power(u, i, pf)


def test_extreme_statistics_do_not_overflow():
    result = analyze_voltage([0, 1e308])
    assert result.mean == pytest.approx(5e307)
    assert result.population_std == pytest.approx(5e307)
    largest = np.finfo(np.float64).max
    constant = analyze_current([largest, largest])
    assert constant.mean == largest
    assert constant.population_std == 0


def test_representable_large_and_tiny_power_and_overflow_rejection():
    for value, expected in ((1e150, 1e300), (1e-150, 1e-300)):
        result = analyze_power([value], [value], [0.6])
        assert result.apparent[0] == pytest.approx(expected, rel=1e-12, abs=0)
        assert result.active[0] == pytest.approx(expected * 0.6, rel=1e-12, abs=0)
        assert result.reactive_abs[0] == pytest.approx(expected * 0.8, rel=1e-12, abs=0)
        assert np.isfinite(result.reactive_abs).all()
    with pytest.raises(AnalysisError, match="可表示范围"):
        analyze_power([np.finfo(float).max], [2], [0.9])


def test_near_unity_pf_uses_stable_formula():
    pf = np.nextafter(1.0, 0.0)
    result = analyze_power([220], [10], [pf])
    with localcontext() as context:
        context.prec = 60
        exact_pf = Decimal.from_float(float(pf))
        reference = float(Decimal(2200) * (1 - exact_pf * exact_pf).sqrt())
    assert result.reactive_abs[0] >= 0
    assert result.reactive_abs[0] == pytest.approx(reference, rel=1e-12, abs=0)


def test_power_series_statistics_and_input_immutability():
    u = np.array([100.0, 200.0, 300.0])
    result = analyze_power(u, [1, 2, 3], [0, 0.6, 1])
    np.testing.assert_allclose(result.active, [0, 240, 900])
    np.testing.assert_allclose(result.apparent, [100, 400, 900])
    np.testing.assert_allclose(result.reactive_abs, [100, 320, 0])
    assert result.active_statistics.mean == pytest.approx(380)
    assert result.active_statistics.minimum == 0
    assert result.active_statistics.maximum == 900
    assert result.apparent_statistics.mean == pytest.approx(1400 / 3)
    assert result.reactive_abs_statistics.mean == pytest.approx(140)
    np.testing.assert_array_equal(u, [100, 200, 300])
    assert not result.active.flags.writeable
