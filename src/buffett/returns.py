"""Model §5: ROE, ROIC and the most important metric, ROIIC.

  ROE    = net income / average common equity
  NOPAT  = EBIT x (1 - normalized tax rate)
  IC     = debt + equity - excess cash
  ROIC   = NOPAT / average invested capital
  ROIIC5 = (NOPAT_t - NOPAT_t-5) / (IC_t - IC_t-5)

Conventions (stated so they can be argued with):
* Normalized tax rate = sum of tax / sum of pretax income over the last five
  years, clamped to [10%, 35%].
* Excess cash = cash + short-term investments - 2% of revenue (operating cash).
* Operating leases are left out of invested capital. Lease cost is already an
  operating expense inside EBIT, and leases only reached the balance sheet in
  2019 (ASC 842), so including them would create an artificial jump in IC.
  They *are* included in the balance-sheet leverage test (balance_sheet.py).
* A ratio over non-positive equity or invested capital is reported as None
  ("not meaningful"), never as a huge or negative percentage. Buybacks can
  drive equity negative (Waters FY2019) without the business being impaired.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .normalize import Financials

OPERATING_CASH_PCT = 0.02


@dataclass
class Returns:
    tax_rate: float
    nopat: list[float | None]
    invested_capital: list[float | None]
    excess_cash: list[float | None]
    roe: list[float | None]
    roic: list[float | None]
    roiic_5y: float | None
    reinvestment_rate_5y: float | None   # b: share of NOPAT retained as new invested capital
    roiic_note: str = ""


def _avg(a, b):
    return None if a is None or b is None else (a + b) / 2


def normalized_tax_rate(f: Financials, years: int = 5) -> float:
    tax = [t for t in f["income_tax"][-years:] if t is not None]
    pre = [p for p in f["pretax_income"][-years:] if p is not None]
    if not tax or not pre or sum(pre) <= 0:
        return 0.21
    return min(max(sum(tax) / sum(pre), 0.10), 0.35)


def compute(f: Financials, span: int = 5) -> Returns:
    n = len(f.years)
    tax = normalized_tax_rate(f)
    ebit = f["operating_income"]
    nopat = [e * (1 - tax) if e is not None else None for e in ebit]

    excess, ic = [], []
    for i in range(n):
        cash, sti, rev = f["cash"][i], f["st_investments"][i], f["revenue"][i]
        if cash is None or rev is None:
            excess.append(None); ic.append(None); continue
        x = max(cash + (sti or 0.0) - OPERATING_CASH_PCT * rev, 0.0)
        excess.append(x)
        debt = (f["long_term_debt"][i] or 0.0) + (f["short_term_debt"][i] or 0.0)
        eq = f["equity"][i]
        ic.append(None if eq is None else debt + eq - x)

    roe, roic = [None], [None]
    for i in range(1, n):
        eq = _avg(f["equity"][i], f["equity"][i - 1])
        ni = f["net_income"][i]
        roe.append(ni / eq if ni is not None and eq and eq > 0 else None)
        c = _avg(ic[i], ic[i - 1])
        roic.append(nopat[i] / c if nopat[i] is not None and c and c > 0 else None)

    roiic, b, note = None, None, ""
    if n > span and None not in (nopat[-1], nopat[-1 - span], ic[-1], ic[-1 - span]):
        d_nopat = nopat[-1] - nopat[-1 - span]
        d_ic = ic[-1] - ic[-1 - span]
        cum_nopat = sum(x for x in nopat[-span:] if x is not None)
        if d_ic > 0:
            roiic = d_nopat / d_ic
        else:
            note = (f"invested capital fell by {-d_ic / 1e6:,.0f}M over {span}y while NOPAT changed "
                    f"by {d_nopat / 1e6:,.0f}M; ROIIC not meaningful")
        if cum_nopat > 0:
            b = min(max(d_ic / cum_nopat, 0.0), 1.0)
    return Returns(tax, nopat, ic, excess, roe, roic, roiic, b, note)


def median_of(xs: list[float | None], last: int = 10) -> float | None:
    vals = [x for x in xs[-last:] if x is not None]
    return median(vals) if vals else None
