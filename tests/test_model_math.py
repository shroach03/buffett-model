"""The Model's own numbers as test fixtures (§1, §10, §11)."""

import pytest

from buffett import analysis, balance_sheet, scorecard, valuation
from buffett.valuation import Case

# Model §11: OE/share $6.50, retention 60%, ROIIC 12%, exit at 15x owner earnings.
OEPS, B, ROIIC, EXIT = 6.50, 0.60, 0.12, 15.0


def test_growth_equals_retention_times_roiic():
    # Model §1: 60% x 15% = 9%, 60% x 6% = 3.6%; §11: 60% x 12% = 7.2%
    assert pytest.approx(0.09) == 0.60 * 0.15
    assert pytest.approx(0.036) == 0.60 * 0.06
    assert pytest.approx(0.072) == B * ROIIC


@pytest.mark.parametrize(
    "price, p_oe, yield_, irr",
    [
        (80, 12.3, 0.081, 0.125),
        (100, 15.4, 0.065, 0.097),
        (130, 20.0, 0.050, 0.066),
    ],
)
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
    assert out.ivps == pytest.approx(1000.0)  # 100 / 10%
    assert out.implied_exit_multiple == pytest.approx(10.0)


def test_net_debt_reduces_value_per_share():
    a = valuation.dcf(100.0, 10.0, 0.0, BASE).ivps
    b = valuation.dcf(100.0, 10.0, 200.0, BASE).ivps
    assert a - b == pytest.approx(20.0)


def test_irr_at_intrinsic_value_equals_discount_rate():
    # Internal consistency: the 10% ladder rung *is* base-case intrinsic value.
    oe, shares, nd = 500.0, 100.0, -300.0
    ivps = valuation.dcf(oe, shares, nd, BASE).ivps
    assert valuation.case_irr(ivps, oe / shares, nd / shares, BASE) == pytest.approx(0.10, abs=1e-8)
    assert valuation.case_ladder(0.10, oe / shares, nd / shares, BASE) == pytest.approx(ivps, rel=1e-6)


def test_required_exit_multiple_round_trip():
    oe, shares = 500.0, 100.0
    ivps = valuation.dcf(oe, shares, 0.0, BASE).ivps
    implied = valuation.dcf(oe, shares, 0.0, BASE).implied_exit_multiple
    assert valuation.required_exit_multiple(ivps, oe / shares, 0.0, BASE) == pytest.approx(implied)


def test_reverse_dcf_recovers_growth():
    oe, shares = 500.0, 100.0
    target = valuation.dcf(oe, shares, 0.0, BASE).ivps
    probe = Case("base", 0.10, 1.0, 0.0, 0.025, 0.20, 0.20)
    assert valuation.reverse_dcf(target, oe, shares, 0.0, probe) == pytest.approx(0.08, abs=1e-6)


def _fin(ebit, interest, debt=0.0):
    """Minimal latest-year Financials stand-in for balance_sheet.compute."""
    return {
        "long_term_debt": [debt],
        "short_term_debt": [0.0],
        "operating_leases": [0.0],
        "interest_expense": [interest],
        "operating_income": [ebit],
    }


def test_unknown_ebit_with_interest_scores_zero_coverage_points():
    bs = balance_sheet.compute(_fin(None, 1_000_000.0), 0.0, 100e6, [100e6])
    assert bs.coverage_status == "unknown" and bs.coverage is None
    line = scorecard.balance_sheet(bs)
    assert line.points == 5  # 5 for no net debt, 0 (not 5) for coverage
    assert "coverage unknown" in line.basis


def test_zero_interest_still_scores_full_coverage_points():
    bs = balance_sheet.compute(_fin(50e6, 0.0), 0.0, 100e6, [100e6])
    assert bs.coverage_status == "no_interest"
    line = scorecard.balance_sheet(bs)
    assert line.points == 10
    assert "no interest" in line.basis


def test_debt_gap_is_unknown_not_zero():
    f = _fin(50e6, 1e6)
    f["long_term_debt"] = [None]
    bs = balance_sheet.compute(f, 0.0, 100e6, [100e6])
    assert not bs.debt_known and bs.net_debt is None and bs.net_debt_to_oe is None
    assert "net debt unknown" in scorecard.balance_sheet(bs).basis


def test_unknown_ebit_produces_leverage_warning(monkeypatch):
    real = analysis.build_financials

    def drop_ebit(facts, ticker):
        fin = real(facts, ticker)
        fin["operating_income"][-1] = None
        return fin

    monkeypatch.setattr(analysis, "build_financials", drop_ebit)
    r = analysis.analyze("ROL")
    assert r.bs.coverage_status == "unknown"
    assert "leverage stress test incomplete: debt or interest data missing" in r.warnings
    bs_line = next(line for line in r.lines if line.category == "Balance-sheet strength")
    assert "coverage unknown" in bs_line.basis


def test_custom_hurdle_drives_the_verdict():
    a = analysis.Assumptions(hurdle=0.12)
    r = analysis.analyze("GGG", a=a)
    base = next(c for c in r.cases if c.case == "base")
    shares = r.inputs["shares"]
    price = valuation.case_ladder(0.11, r.normalized_oe / shares, r.inputs["net_debt_dcf"] / shares, base.assumptions)

    r = analysis.analyze("GGG", price=price, a=a)
    assert r.expected_return_irr == pytest.approx(0.11, abs=1e-4)
    assert r.decision.verdict != "CANDIDATE"
    assert "expected return 11.0% < 12% hurdle" in r.decision.reason

    # Same price against the default 10% hurdle: 11% clears it, so no hurdle miss.
    r10 = analysis.analyze("GGG", price=price)
    assert "hurdle" not in r10.decision.reason


def test_verdict_hurdle_argument():
    lines = [
        scorecard.Line("Earnings quality & consistency", 45, 45, ""),
        scorecard.Line("Valuation & expected return", 15, 20, ""),
        scorecard.Line("Margin of safety", 10, 10, ""),
    ]
    j = scorecard.Judgment(15, 10, "test", "2026-01-01")
    assert scorecard.verdict(lines, j, [], 0.11, 0.30).verdict == "CANDIDATE"
    d = scorecard.verdict(lines, j, [], 0.11, 0.30, hurdle=0.12)
    assert d.verdict == "WAIT" and "< 12% hurdle" in d.reason


def test_terminal_growth_at_or_above_discount_rate_raises():
    case = Case(
        "bad", discount_rate=0.02, oe_haircut=1.0, g_start=0.05, g_terminal=0.03, roiic=0.15, roiic_terminal=0.15
    )
    with pytest.raises(ValueError, match="discount rate must exceed terminal growth"):
        valuation.project(6.50, case)
