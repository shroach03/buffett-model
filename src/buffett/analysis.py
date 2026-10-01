"""End-to-end pipeline: XBRL facts -> normalized financials -> the Model's tests
-> valuation -> scorecard -> verdict. Every assumption that is not a direct
Model default is a named parameter in ``Assumptions``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import balance_sheet, consistency, edgar, owner_earnings, returns, scorecard, valuation
from .normalize import Financials, build_financials
from .valuation import Case, CaseResult

DATA = edgar.REPO_ROOT / "data"


@dataclass(frozen=True)
class Assumptions:
    hurdle: float = 0.10  # Model: 10% unless the user updates it
    roiic_cap: float = 0.30  # no base case assumes >30% on new capital
    g_cap: float = 0.12  # no base case assumes >12% starting growth
    peak_guard: float = 1.15  # latest OE > 115% of 3y mean -> use the mean
    window: int = 10


DEFAULT_ASSUMPTIONS = Assumptions()


@dataclass
class Result:
    ticker: str
    fin: Financials
    oe: owner_earnings.OwnerEarnings
    ret: returns.Returns
    cons: consistency.Consistency
    bs: balance_sheet.BalanceSheet
    normalized_oe: float | None
    oeps: float | None
    inputs: dict[str, Any]
    cases: list[CaseResult]
    price: float | None
    price_date: str | None
    expected_return_irr: float | None
    expected_return_eq: float | None
    expected_return_no_rerating: float | None
    reverse_dcf_g: float | None
    ladder: dict[float, float]
    mos: float | None
    lines: list[scorecard.Line]
    decision: scorecard.Decision
    judgment: scorecard.Judgment | None
    warnings: list[str] = field(default_factory=list)


def load_prices(path: Path = DATA / "prices.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"prices": {}}


def load_judgment(ticker: str, directory: Path = DATA / "judgment") -> scorecard.Judgment | None:
    p = directory / f"{ticker.upper()}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    return scorecard.Judgment(
        d["moat"], d["management"], d["source"], d["date"], d.get("fatal_flaws", []), d.get("notes", "")
    )


def _resolve_judgment(ticker: str, judgment: scorecard.Judgment | bool | None) -> scorecard.Judgment | None:
    if judgment is True:
        return load_judgment(ticker)
    if judgment is False:
        return None
    return judgment


def normalized(oe: list[float | None], guard: float) -> float | None:
    recent = [x for x in oe[-3:] if x is not None]
    if not recent:
        return None
    latest, mean3 = recent[-1], sum(recent) / len(recent)
    if latest <= 0:
        return mean3 if mean3 > 0 else None
    return mean3 if latest > guard * mean3 else latest


def analyze(
    ticker: str,
    facts: dict | None = None,
    price: float | None = None,
    judgment: scorecard.Judgment | bool | None = True,
    a: Assumptions = DEFAULT_ASSUMPTIONS,
) -> Result:
    facts = facts or edgar.load_snapshot(ticker)
    fin = build_financials(facts, ticker)
    warnings: list[str] = []

    oe = owner_earnings.compute(fin)
    ret = returns.compute(fin)
    cons = consistency.compute(oe.owner_earnings, oe.oe_per_share, fin["net_income"], a.window)
    norm_oe = normalized(oe.owner_earnings, a.peak_guard)
    shares = fin["diluted_shares"][-1] or next((s for s in reversed(fin["diluted_shares"]) if s), None)
    oeps = norm_oe / shares if norm_oe and shares else None
    bs = balance_sheet.compute(fin, ret.excess_cash[-1] or 0.0, norm_oe, oe.owner_earnings, a.window)

    if cons.years_available < a.window:
        warnings.append(
            f"only {cons.years_available} of {a.window} years of owner earnings computable "
            f"(missing inputs are left unknown, not estimated)"
        )

    inputs, b_hist = _valuation_inputs(ret, bs, shares, a, warnings)
    cases = _build_cases(norm_oe, shares, inputs, b_hist, ret.roiic_5y, a)
    price, price_date = _resolve_price(ticker, price)
    po = _price_outputs(price, norm_oe, inputs, cases, warnings)
    judgment = _resolve_judgment(ticker, judgment)
    lines, decision = _score(ret, cons, bs, inputs, po, judgment, a)

    known = (ticker.upper(), fin, oe, ret, cons, bs, norm_oe, oeps, inputs, cases, price, price_date)
    priced = (po.irr, po.eq, po.no_rerating, po.reverse_dcf_g, po.ladder, po.mos)
    return Result(*known, *priced, lines, decision, judgment, warnings)


def _valuation_inputs(
    ret: returns.Returns, bs: balance_sheet.BalanceSheet, shares: float | None, a: Assumptions, warnings: list[str]
) -> tuple[dict[str, Any], float]:
    """Base-case ROIIC, reinvestment rate and growth; returns (inputs, historical b)."""
    roic_med = returns.median_of(ret.roic, a.window)
    roe_med = returns.median_of(ret.roe, a.window)
    candidates = [x for x in (ret.roiic_5y, roic_med) if x is not None]
    roiic_base = min(min(candidates), a.roiic_cap) if candidates else None
    b_hist = ret.reinvestment_rate_5y if ret.reinvestment_rate_5y is not None else 0.0
    if roiic_base is not None and roiic_base <= 0.02:
        warnings.append("incremental returns near zero: valued as a no-growth business")
        roiic_base, b_hist = a.hurdle, 0.0
    g_base = min(b_hist * roiic_base, a.g_cap) if roiic_base else 0.0
    b_base = g_base / roiic_base if roiic_base else 0.0
    net_debt_dcf = bs.total_debt - bs.excess_cash  # leases excluded: lease cost is already in OE
    inputs = {
        "roiic_5y": ret.roiic_5y,
        "roic_median": roic_med,
        "roe_median": roe_med,
        "roiic_base": roiic_base,
        "b_hist": ret.reinvestment_rate_5y,
        "b_base": b_base,
        "g_base": g_base,
        "tax_rate": ret.tax_rate,
        "net_debt_dcf": net_debt_dcf,
        "shares": shares,
    }
    return inputs, b_hist


def _build_cases(
    norm_oe: float | None,
    shares: float | None,
    inputs: dict[str, Any],
    b_hist: float,
    roiic_5y: float | None,
    a: Assumptions,
) -> list[CaseResult]:
    """Bear / base / bull DCFs (Model §10); empty when OE, shares or ROIIC are unknown."""
    roiic_base, g_base = inputs["roiic_base"], inputs["g_base"]
    if not (norm_oe and shares and roiic_base):
        return []
    hist = min(roiic_5y if roiic_5y is not None else roiic_base, 0.40)
    base_case = Case("base", a.hurdle, 1.0, g_base, 0.025, roiic_base, roiic_base)
    bear_roiic = max(0.6 * roiic_base, 0.01)
    specs = [
        Case("bear", a.hurdle + 0.02, 0.90, min(0.5 * g_base, bear_roiic), 0.015, bear_roiic, a.hurdle + 0.02),
        base_case,
        Case(
            "bull",
            a.hurdle,
            1.0,
            min(b_hist * max(hist, roiic_base), 0.15),
            0.03,
            max(hist, roiic_base),
            max(hist, roiic_base),
            hold_years=5,
        ),
    ]
    return [valuation.dcf(norm_oe, shares, inputs["net_debt_dcf"], c) for c in specs]


def _resolve_price(ticker: str, price: float | None) -> tuple[float | None, str | None]:
    """An explicit price has no date; otherwise use the bundled price file."""
    if price is not None:
        return price, None
    pinfo = load_prices()
    return pinfo["prices"].get(ticker.upper()), pinfo.get("as_of")


@dataclass
class _PriceOutputs:
    irr: float | None = None
    eq: float | None = None
    no_rerating: float | None = None
    reverse_dcf_g: float | None = None
    mos: float | None = None
    ladder: dict[float, float] = field(default_factory=dict)


def _price_outputs(
    price: float | None, norm_oe: float | None, inputs: dict[str, Any], cases: list[CaseResult], warnings: list[str]
) -> _PriceOutputs:
    """Price-dependent outputs. The conservative expected return is the ten-year
    IRR of the *base case* (same growth path and Gordon terminal value as the
    DCF), so the 10% ladder rung equals base-case intrinsic value and every
    number on the card agrees."""
    po = _PriceOutputs()
    shares = inputs["shares"]
    if not (cases and norm_oe and shares):
        return po
    oeps = norm_oe / shares
    nd_ps = inputs["net_debt_dcf"] / shares
    base = next(c for c in cases if c.case == "base")
    try:
        po.ladder = {t: valuation.case_ladder(t, oeps, nd_ps, base.assumptions) for t in (0.08, 0.10, 0.12, 0.15)}
    except ValueError:
        warnings.append("price ladder not computable: the base-case IRR could not be solved")
    if price:
        _returns_at_price(po, price, norm_oe, oeps, nd_ps, inputs, base, warnings)
    return po


def _returns_at_price(
    po: _PriceOutputs,
    price: float,
    norm_oe: float,
    oeps: float,
    nd_ps: float,
    inputs: dict[str, Any],
    base: CaseResult,
    warnings: list[str],
) -> None:
    """Fill ``po`` with the IRRs, reverse DCF and margin of safety at ``price``;
    add p_oe and the exit multiples to ``inputs``."""
    case = base.assumptions
    m0 = (price + nd_ps) / oeps
    req_mult = None
    try:
        po.irr = valuation.case_irr(price, oeps, nd_ps, case)
        # The shorthand takes a fractional power of M10/M0, undefined when price < net cash/share.
        if m0 > 0:
            po.eq = valuation.expected_return_equation(
                price + nd_ps, oeps, inputs["b_base"], case.roiic, base.implied_exit_multiple
            )
        po.no_rerating = valuation.case_irr(price, oeps, nd_ps, case, exit_multiple=m0)
        po.reverse_dcf_g = valuation.reverse_dcf(price, norm_oe, inputs["shares"], inputs["net_debt_dcf"], case)
        req_mult = valuation.required_exit_multiple(price, oeps, nd_ps, case)
    except ValueError:
        po.irr = po.eq = po.no_rerating = po.reverse_dcf_g = req_mult = None
        warnings.append(
            f"expected return not computable at a price of {price:,.2f}: "
            "the ten-year IRR has no solution in the searched range"
        )
    po.mos = 1 - price / base.ivps if base.ivps > 0 else None
    inputs.update(p_oe=m0, required_exit_multiple=req_mult, base_exit_multiple=base.implied_exit_multiple)


def _score(
    ret: returns.Returns,
    cons: consistency.Consistency,
    bs: balance_sheet.BalanceSheet,
    inputs: dict[str, Any],
    po: _PriceOutputs,
    judgment: scorecard.Judgment | None,
    a: Assumptions,
) -> tuple[list[scorecard.Line], scorecard.Decision]:
    """Model §2 scorecard lines and the verdict."""
    roic_min = min((x for x in ret.roic[-a.window :] if x is not None), default=None)
    now, then = ret.nopat[-1], ret.nopat[-6]
    nopat_grew = now is not None and then is not None and now > then
    lines = [
        scorecard.earnings_quality(cons),
        scorecard.returns_on_capital(inputs["roe_median"], inputs["roic_median"], ret.roiic_5y, roic_min, nopat_grew),
        scorecard.balance_sheet(bs),
        scorecard.valuation(po.irr),
        scorecard.margin_of_safety(po.mos),
    ]
    fatal = []
    if bs.leverage_fatal:
        fatal.append("leverage under adverse conditions (stressed net debt > 3x OE or coverage < 3x)")
    return lines, scorecard.verdict(lines, judgment, fatal, po.irr, po.mos)
