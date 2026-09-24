"""The Model's own numbers as test fixtures (§1, §10, §11)."""
import pytest

from buffett import valuation
from buffett.valuation import Case

# Model §11: OE/share $6.50, retention 60%, ROIIC 12%, exit at 15x owner earnings.
OEPS, B, ROIIC, EXIT = 6.50, 0.60, 0.12, 15.0


def test_growth_equals_retention_times_roiic():
    # Model §1: 60% x 15% = 9%, 60% x 6% = 3.6%; §11: 60% x 12% = 7.2%
    assert 0.60 * 0.15 == pytest.approx(0.09)
    assert 0.60 * 0.06 == pytest.approx(0.036)
    assert B * ROIIC == pytest.approx(0.072)


@pytest.mark.parametrize("price, p_oe, yield_, irr", [
    (80, 12.3, 0.081, 0.125),
    (100, 15.4, 0.065, 0.097),
    (130, 20.0, 0.050, 0.066),
])
def test_section11_table(price, p_oe, yield_, irr):
    assert price / OEPS == pytest.approx(p_oe, abs=0.05)
    assert OEPS / price == pytest.approx(yield_, abs=0.0006)
    # The Model's table rounds to one decimal; 9.75% prints as 9.7 there.
    assert valuation.ten_year_irr(price, OEPS, B, ROIIC, EXIT) == pytest.approx(irr, abs=0.0006)


def test_expected_return_equation_close_to_irr():
    # The §1 shorthand should land within ~0.5pp of the exact IRR on the §11 example.
    for price in (80, 100, 130):
        eq = valuation.expected_return_equation(price, OEPS, B, ROIIC, EXIT)
        exact = valuation.ten_year_irr(price, OEPS, B, ROIIC, EXIT)
        assert abs(eq - exact) < 0.005


def test_ladder_inverts_irr():
    for target in (0.08, 0.10, 0.12, 0.15):
        p = valuation.ladder_price(target, OEPS, B, ROIIC, EXIT)
        assert valuation.ten_year_irr(p, OEPS, B, ROIIC, EXIT) == pytest.approx(target, abs=1e-6)


def test_irr_simple():
    assert valuation.irr([-100, 110]) == pytest.approx(0.10)
    assert valuation.irr([-100, 0, 121]) == pytest.approx(0.10)


BASE = Case("base", 0.10, 1.0, 0.08, 0.025, 0.20, 0.20)


def test_no_double_counting_growth_and_distribution():
    # Growth is paid for by retention: distributable = OE x (1 - g/ROIIC).
    proj = valuation.project(100.0, BASE)
    for p in proj["path"]:
        assert p["b"] == pytest.approx(p["g"] / BASE.roiic)
        assert p["distributable"] == pytest.approx(p["oe"] * (1 - p["b"]))


def test_zero_growth_dcf_is_a_perpetuity():
    flat = Case("flat", 0.10, 1.0, 0.0, 0.0, 0.20, 0.20)
    out = valuation.dcf(100.0, 1.0, 0.0, flat)
    assert out["ivps"] == pytest.approx(1000.0)          # 100 / 10%
    assert out["implied_exit_multiple"] == pytest.approx(10.0)


def test_net_debt_reduces_value_per_share():
    a = valuation.dcf(100.0, 10.0, 0.0, BASE)["ivps"]
    b = valuation.dcf(100.0, 10.0, 200.0, BASE)["ivps"]
    assert a - b == pytest.approx(20.0)


def test_irr_at_intrinsic_value_equals_discount_rate():
    # Internal consistency: the 10% ladder rung *is* base-case intrinsic value.
    oe, shares, nd = 500.0, 100.0, -300.0
    ivps = valuation.dcf(oe, shares, nd, BASE)["ivps"]
    assert valuation.case_irr(ivps, oe / shares, nd / shares, BASE) == pytest.approx(0.10, abs=1e-8)
    assert valuation.case_ladder(0.10, oe / shares, nd / shares, BASE) == pytest.approx(ivps, rel=1e-6)


def test_required_exit_multiple_round_trip():
    oe, shares = 500.0, 100.0
    ivps = valuation.dcf(oe, shares, 0.0, BASE)["ivps"]
    implied = valuation.dcf(oe, shares, 0.0, BASE)["implied_exit_multiple"]
    assert valuation.required_exit_multiple(ivps, oe / shares, 0.0, BASE) == pytest.approx(implied)


def test_reverse_dcf_recovers_growth():
    oe, shares = 500.0, 100.0
    target = valuation.dcf(oe, shares, 0.0, BASE)["ivps"]
    probe = Case("base", 0.10, 1.0, 0.0, 0.025, 0.20, 0.20)
    assert valuation.reverse_dcf(target, oe, shares, 0.0, probe) == pytest.approx(0.08, abs=1e-6)
