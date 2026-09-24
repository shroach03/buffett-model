"""Model §2: the 100-point scorecard and decision rule.

Code scores the five categories that financial data can measure (75 points).
The other two, understandability & moat (15) and management & allocation (10),
are judgment. They come from a ``Judgment`` record with a named source, and if
none is supplied the verdict says so instead of inventing a score. The
point bands inside each category are this project's operationalization of
the Model's "practical starting standards"; they live in one place so they can
be argued with and changed.

Decision rule (Model §2): quality >= 55/70, total >= 75, no fatal flaw,
conservative expected return >= hurdle, margin of safety >= 20%.
Verdicts: PASS (quality gate or fatal flaw fails), WAIT (quality passes, price
doesn't), CANDIDATE (all gates pass: a recommendation to *study*, never to buy).
"""
from __future__ import annotations

from dataclasses import dataclass, field

HURDLE = 0.10
MIN_MOS = 0.20


@dataclass
class Judgment:
    moat: int                 # 0-15
    management: int           # 0-10
    source: str
    date: str
    fatal_flaws: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Line:
    category: str
    points: float
    max_points: int
    basis: str


def band(x, bands):
    """bands: list of (threshold, points) checked in order with x >= threshold."""
    if x is None:
        return 0
    for threshold, pts in bands:
        if x >= threshold:
            return pts
    return 0


def earnings_quality(c) -> Line:
    pos = 5 if c.positive_years >= 9 else 3 if c.positive_years >= 8 else 0
    if c.years_available < 10:
        pos = round(pos * c.years_available / 10)
    growth = band(c.oeps_cagr, [(0.10, 4), (0.06, 3), (0.03, 2), (0.0001, 1)])
    dd = 3 if c.worst_peak_to_trough is None else band(c.worst_peak_to_trough, [(-0.15, 3), (-0.30, 2), (-0.50, 1)])
    conv = band(c.cash_conversion, [(0.80, 3), (0.60, 1)])
    basis = (f"{c.positive_years}/{c.years_available} positive OE yrs; OEPS CAGR "
             f"{_pct(c.oeps_cagr)}; worst drawdown {_pct(c.worst_peak_to_trough)}; conversion {_x(c.cash_conversion)}")
    return Line("Earnings quality & consistency", pos + growth + dd + conv, 15, basis)


def returns_on_capital(roe_med, roic_med, roiic, roic_min, nopat_grew) -> Line:
    p = band(roe_med, [(0.15, 5), (0.10, 3)])
    p += band(roic_med, [(0.20, 7), (0.12, 5), (0.08, 2)])
    if roiic is None:
        p += 3 if nopat_grew else 0
    else:
        p += band(roiic, [(0.15, 5), (0.12, 4), (0.08, 2)])
    p += band(roic_min, [(0.10, 3), (0.06, 1)])
    basis = (f"median ROE {_pct(roe_med)}; median ROIC {_pct(roic_med)}; 5y ROIIC "
             f"{_pct(roiic) if roiic is not None else 'n/m'}; worst ROIC {_pct(roic_min)}")
    return Line("Returns on capital", p, 20, basis)


def balance_sheet(bs) -> Line:
    lev = bs.net_debt_to_oe
    p = 5 if bs.net_debt <= 0 else band(-lev if lev is not None else None, [(-1, 4), (-2, 3), (-3, 1)])
    p += 5 if bs.coverage is None else band(bs.coverage, [(12, 5), (6, 4), (3, 2)])
    basis = (f"net debt incl. leases {bs.net_debt / 1e6:,.0f}M = {_x(lev)} OE; coverage "
             f"{'no interest' if bs.coverage is None else f'{bs.coverage:.0f}x'}")
    return Line("Balance-sheet strength", p, 10, basis)


def valuation(expected_return) -> Line:
    p = band(expected_return, [(0.15, 20), (0.12, 17), (0.10, 14), (0.08, 9), (0.06, 5), (0.04, 2)])
    return Line("Valuation & expected return", p, 20, f"conservative 10y IRR {_pct(expected_return)}")


def margin_of_safety(mos) -> Line:
    p = band(mos, [(0.30, 10), (0.20, 8), (0.10, 5), (0.0, 3), (-0.15, 1)])
    return Line("Margin of safety", p, 10, f"discount to base-case IV {_pct(mos)}")


def verdict(lines: list[Line], judgment: Judgment | None, fatal: list[str],
            expected_return, mos) -> dict:
    quant = {l.category: l.points for l in lines}
    quant_quality = sum(v for k, v in quant.items() if k not in ("Valuation & expected return", "Margin of safety"))
    price_pts = quant.get("Valuation & expected return", 0) + quant.get("Margin of safety", 0)
    price_ok = (expected_return is not None and expected_return >= HURDLE and mos is not None and mos >= MIN_MOS)
    fatal = list(fatal) + (judgment.fatal_flaws if judgment else [])

    if judgment is None:
        max_quality = quant_quality + 25
        if max_quality < 55 or fatal:
            v = "PASS"
            why = "fatal flaw" if fatal else f"quality cannot reach 55 even with full judgment points ({max_quality}/70 max)"
        else:
            v = "NEEDS JUDGMENT"
            why = (f"measurable quality {quant_quality}/45; moat and management (25 pts) need a judgment input. "
                   f"Price test {'passes' if price_ok else 'fails'}, so the best possible verdict is "
                   f"{'CANDIDATE' if price_ok else 'WAIT'}")
        return {"verdict": v, "reason": why, "quality": None, "total": None, "fatal": fatal,
                "quant_quality": quant_quality, "price_points": price_pts}

    quality = quant_quality + judgment.moat + judgment.management
    total = quality + price_pts
    if fatal:
        v, why = "PASS", "fatal flaw: " + "; ".join(fatal)
    elif quality < 55:
        v, why = "PASS", f"quality {quality}/70 < 55"
    elif total >= 75 and price_ok:
        v, why = "CANDIDATE", "all gates pass: study it, don't buy it"
    else:
        misses = []
        if expected_return is None or expected_return < HURDLE:
            misses.append(f"expected return {_pct(expected_return)} < {HURDLE:.0%} hurdle")
        if mos is None or mos < MIN_MOS:
            misses.append(f"margin of safety {_pct(mos)} < {MIN_MOS:.0%}")
        if total < 75:
            misses.append(f"total {total}/100 < 75")
        v, why = "WAIT", "quality passes; " + "; ".join(misses)
    return {"verdict": v, "reason": why, "quality": quality, "total": total, "fatal": fatal,
            "quant_quality": quant_quality, "price_points": price_pts}


def _pct(x):
    return "n/a" if x is None else f"{x:.1%}"


def _x(x):
    return "n/a" if x is None else f"{x:.2f}x"
