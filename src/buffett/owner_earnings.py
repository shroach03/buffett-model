"""Model §3: owner earnings, not reported EPS.

Two versions, as the Model specifies:

* Conservative FCF = CFO - total capex - stock-based compensation.
  (CFO adds SBC back as "non-cash"; the Model says treat it as a real cost, so
  it is deducted again here. Otherwise SBC would be added back while its
  dilution is ignored, which is exactly what the Model forbids.)

* Buffett owner earnings
  OE = net income + D&A + non-cash impairments
       - estimated maintenance capex - normalized working-capital requirement.
  Net income already has SBC expensed, so OE treats it as a cost too.

Maintenance capex is not a reported number. Estimate used (documented,
deliberately conservative):
  growth capex  = (trailing PP&E / sales) x max(sales increase, 0)
  maintenance   = max(capex - growth capex, min(capex, D&A)), capped at capex
The floor means a company is never assumed to maintain its assets for less
than its D&A charge (or its whole capex, if smaller). For asset-light firms
where D&A exceeds capex, maintenance capex = all capex.

Working-capital requirement:
  operating WC = (current assets - cash - short-term investments) - current liabilities
  required increase = max(median(OWC / sales, trailing 5y) x sales increase, 0)
Using a normalized ratio rather than the raw yearly change keeps one noisy
year-end from swinging owner earnings.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .normalize import Financials


def _sub(*xs):
    """a - b - c ... ; None if any input is None."""
    if any(x is None for x in xs):
        return None
    out = xs[0]
    for x in xs[1:]:
        out -= x
    return out


@dataclass
class OwnerEarnings:
    conservative_fcf: list[float | None]
    maintenance_capex: list[float | None]
    growth_capex: list[float | None]
    wc_requirement: list[float | None]
    owner_earnings: list[float | None]
    oe_per_share: list[float | None]


def compute(f: Financials, lookback: int = 5) -> OwnerEarnings:
    n = len(f.years)
    rev, capex, da, ni = f["revenue"], f["capex"], f["da"], f["net_income"]
    cfo, sbc, shares = f["cfo"], f["sbc"], f["diluted_shares"]
    imp = f.data.get("impairments", [0.0] * n)
    ca, cl, cash, sti = f["current_assets"], f["current_liabilities"], f["cash"], f["st_investments"]
    ppe = f["ppe_net"]

    fcf = [_sub(cfo[i], capex[i], sbc[i]) for i in range(n)]

    owc = []
    for i in range(n):
        v = _sub(ca[i], cash[i], sti[i], cl[i])
        owc.append(v)

    maint, growth, wcreq, oe, oeps = [], [], [], [], []
    for i in range(n):
        if i == 0 or None in (rev[i], rev[i - 1], capex[i], da[i]):
            maint.append(None); growth.append(None); wcreq.append(None); oe.append(None); oeps.append(None)
            continue
        window = range(max(0, i - lookback + 1), i + 1)
        intensities = [ppe[j] / rev[j] for j in window if ppe[j] is not None and rev[j]]
        d_sales = max(rev[i] - rev[i - 1], 0.0)
        g_capex = (sum(intensities) / len(intensities)) * d_sales if intensities else 0.0
        g_capex = min(g_capex, capex[i])
        m = max(capex[i] - g_capex, min(capex[i], da[i]))
        m = min(m, capex[i])

        ratios = [owc[j] / rev[j] for j in window if owc[j] is not None and rev[j]]
        wc = max(median(ratios) * d_sales, 0.0) if ratios else None

        o = None
        if ni[i] is not None and wc is not None:
            o = ni[i] + da[i] + (imp[i] or 0.0) - m - wc
        maint.append(m); growth.append(capex[i] - m); wcreq.append(wc); oe.append(o)
        oeps.append(o / shares[i] if o is not None and shares[i] else None)

    return OwnerEarnings(fcf, maint, growth, wcreq, oe, oeps)
