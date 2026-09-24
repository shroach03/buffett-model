"""End-to-end pipeline: XBRL facts -> normalized financials -> the Model's tests
-> valuation -> scorecard -> verdict. Every assumption that is not a direct
Model default is a named parameter in ``Assumptions``."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import balance_sheet, consistency, edgar, owner_earnings, returns, scorecard, valuation
from .normalize import Financials, build_financials
from .valuation import Case

DATA = edgar.REPO_ROOT / "data"


@dataclass(frozen=True)
class Assumptions:
    hurdle: float = 0.10              # Model: 10% unless the user updates it
    roiic_cap: float = 0.30           # no base case assumes >30% on new capital
    g_cap: float = 0.12               # no base case assumes >12% starting growth
    peak_guard: float = 1.15          # latest OE > 115% of 3y mean -> use the mean
    window: int = 10


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
    inputs: dict
    cases: list[dict]
    price: float | None
    price_date: str | None
    expected_return_irr: float | None
    expected_return_eq: float | None
    expected_return_no_rerating: float | None
    reverse_dcf_g: float | None
    ladder: dict
    mos: float | None
    lines: list[scorecard.Line]
    decision: dict
    judgment: scorecard.Judgment | None
    warnings: list[str] = field(default_factory=list)


def load_prices(path: Path = DATA / "prices.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"prices": {}}


def load_judgment(ticker: str, directory: Path = DATA / "judgment") -> scorecard.Judgment | None:
    p = directory / f"{ticker.upper()}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    return scorecard.Judgment(d["moat"], d["management"], d["source"], d["date"],
                              d.get("fatal_flaws", []), d.get("notes", ""))


def normalized(oe: list[float | None], guard: float) -> float | None:
    recent = [x for x in oe[-3:] if x is not None]
    if not recent:
        return None
    latest, mean3 = recent[-1], sum(recent) / len(recent)
    if latest <= 0:
        return mean3 if mean3 > 0 else None
    return mean3 if latest > guard * mean3 else latest


def analyze(ticker: str, facts: dict | None = None, price: float | None = None,
            judgment: scorecard.Judgment | None | bool = True, a: Assumptions = Assumptions()) -> Result:
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
        warnings.append(f"only {cons.years_available} of {a.window} years of owner earnings computable "
                        f"(missing inputs are left unknown, not estimated)")

    # --- valuation inputs -------------------------------------------------------
    roic_med = returns.median_of(ret.roic, a.window)
    roe_med = returns.median_of(ret.roe, a.window)
    roic_min = min((x for x in ret.roic[-a.window:] if x is not None), default=None)
    candidates = [x for x in (ret.roiic_5y, roic_med) if x is not None]
    roiic_base = min(min(candidates), a.roiic_cap) if candidates else None
    b_hist = ret.reinvestment_rate_5y if ret.reinvestment_rate_5y is not None else 0.0
    if roiic_base is not None and roiic_base <= 0.02:
        warnings.append("incremental returns near zero: valued as a no-growth business")
        roiic_base, b_hist = a.hurdle, 0.0
    g_base = min(b_hist * roiic_base, a.g_cap) if roiic_base else 0.0
    b_base = g_base / roiic_base if roiic_base else 0.0
    net_debt_dcf = bs.total_debt - bs.excess_cash   # leases excluded: lease cost is already in OE
    inputs = dict(roiic_5y=ret.roiic_5y, roic_median=roic_med, roe_median=roe_med, roiic_base=roiic_base,
                  b_hist=ret.reinvestment_rate_5y, b_base=b_base, g_base=g_base, tax_rate=ret.tax_rate,
                  net_debt_dcf=net_debt_dcf, shares=shares)

    cases, base_case = [], None
    if norm_oe and shares and roiic_base:
        hist = min(ret.roiic_5y if ret.roiic_5y is not None else roiic_base, 0.40)
        base_case = Case("base", a.hurdle, 1.0, g_base, 0.025, roiic_base, roiic_base)
        bear_roiic = max(0.6 * roiic_base, 0.01)
        specs = [
            Case("bear", a.hurdle + 0.02, 0.90, min(0.5 * g_base, bear_roiic), 0.015, bear_roiic, a.hurdle + 0.02),
            base_case,
            Case("bull", a.hurdle, 1.0, min(b_hist * max(hist, roiic_base), 0.15), 0.03,
                 max(hist, roiic_base), max(hist, roiic_base), hold_years=5),
        ]
        cases = [valuation.dcf(norm_oe, shares, net_debt_dcf, c) for c in specs]

    # --- price-dependent outputs ---------------------------------------------------
    # The conservative expected return is the ten-year IRR of the *base case*
    # (same growth path and Gordon terminal value as the DCF), so the 10% ladder
    # rung equals base-case intrinsic value and every number on the card agrees.
    price_date = None
    if price is None:
        pinfo = load_prices()
        price = pinfo["prices"].get(ticker.upper())
        price_date = pinfo.get("as_of")
    r_irr = r_eq = r_flat = rev_g = req_mult = mos = None
    ladder = {}
    if base_case and oeps:
        nd_ps = net_debt_dcf / shares
        base = next(c for c in cases if c["case"] == "base")
        ladder = {t: valuation.case_ladder(t, oeps, nd_ps, base_case) for t in (0.08, 0.10, 0.12, 0.15)}
        if price:
            r_irr = valuation.case_irr(price, oeps, nd_ps, base_case)
            m0 = (price + nd_ps) / oeps
            r_eq = valuation.expected_return_equation(price + nd_ps, oeps, b_base, roiic_base,
                                                      base["implied_exit_multiple"])
            r_flat = valuation.case_irr(price, oeps, nd_ps, base_case, exit_multiple=m0)
            rev_g = valuation.reverse_dcf(price, norm_oe, shares, net_debt_dcf, base_case)
            req_mult = valuation.required_exit_multiple(price, oeps, nd_ps, base_case)
            mos = 1 - price / base["ivps"] if base["ivps"] > 0 else None
            inputs.update(p_oe=m0, required_exit_multiple=req_mult,
                          base_exit_multiple=base["implied_exit_multiple"])

    # --- scorecard -------------------------------------------------------------------
    nopat_grew = None not in (ret.nopat[-1], ret.nopat[-6]) and ret.nopat[-1] > ret.nopat[-6]
    lines = [
        scorecard.earnings_quality(cons),
        scorecard.returns_on_capital(roe_med, roic_med, ret.roiic_5y, roic_min, nopat_grew),
        scorecard.balance_sheet(bs),
        scorecard.valuation(r_irr),
        scorecard.margin_of_safety(mos),
    ]
    fatal = []
    if bs.leverage_fatal:
        fatal.append("leverage under adverse conditions (stressed net debt > 3x OE or coverage < 3x)")
    if judgment is True:
        judgment = load_judgment(ticker)
    elif judgment is False:
        judgment = None
    decision = scorecard.verdict(lines, judgment, fatal, r_irr, mos)

    return Result(ticker.upper(), fin, oe, ret, cons, bs, norm_oe, oeps, inputs, cases, price, price_date,
                  r_irr, r_eq, r_flat, rev_g, ladder, mos, lines, decision, judgment, warnings)
