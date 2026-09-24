"""Model §9: debt under adverse, not average, conditions.

  Net debt          = total debt + operating leases - excess cash
  Net debt / OE     < ~2x normalized owner earnings
  Interest coverage = EBIT / interest  > 6x

The adverse-conditions test (the Model: test debt on recessionary earnings,
not current ones) applies the company's own worst one-year percentage decline
in EBIT and in owner earnings over the last ten years to today's figures.
Using the worst *level* instead would compare today's debt with a decade-old
trough from a much smaller business.

Fatal-flaw trigger (this project's operationalization of "leverage that can
turn a temporary problem into permanent loss"): stressed net debt above 3x
stressed owner earnings, or stressed coverage below 3x.

Not covered by XBRL company facts and therefore not tested here: pensions
beyond what is on the balance sheet, supplier financing, factored
receivables, guarantees, litigation and maturity concentration. These belong
in the judgment layer and are listed as such in the report.
"""
from __future__ import annotations

from dataclasses import dataclass

from .normalize import Financials


@dataclass
class BalanceSheet:
    total_debt: float
    operating_leases: float
    excess_cash: float
    net_debt: float                 # incl. leases, less excess cash
    net_debt_to_oe: float | None
    coverage: float | None          # None = no interest expense (effectively infinite)
    stressed_net_debt_to_oe: float | None
    stressed_coverage: float | None
    leverage_fatal: bool


def worst_decline(series: list[float | None]) -> float:
    """Worst one-year percentage change (<= 0) in a series, skipping gaps."""
    worst = 0.0
    for a, b in zip(series, series[1:]):
        if a is not None and b is not None and a > 0:
            worst = min(worst, b / a - 1)
    return max(worst, -1.0)


def compute(f: Financials, excess_cash: float, normalized_oe: float | None,
            oe_history: list[float | None], window: int = 10) -> BalanceSheet:
    debt = (f["long_term_debt"][-1] or 0.0) + (f["short_term_debt"][-1] or 0.0)
    leases = f["operating_leases"][-1] or 0.0
    net = debt + leases - excess_cash
    interest = f["interest_expense"][-1] or 0.0
    ebit = f["operating_income"][-1]

    def ratio(nd, oe):
        if oe is None:
            return None
        if nd <= 0:
            return nd / oe if oe > 0 else None
        return nd / oe if oe > 0 else float("inf")

    cov = ebit / interest if interest > 0 and ebit is not None else None
    stressed_ebit = None if ebit is None else ebit * (1 + worst_decline(f["operating_income"][-window:]))
    stressed_oe = None if normalized_oe is None else normalized_oe * (1 + worst_decline(oe_history[-window:]))
    s_cov = stressed_ebit / interest if interest > 0 and stressed_ebit is not None else None
    s_lev = ratio(net, stressed_oe)
    lev = ratio(net, normalized_oe)

    fatal = (s_lev is not None and s_lev > 3.0) or (s_cov is not None and s_cov < 3.0)
    return BalanceSheet(debt, leases, excess_cash, net, lev, cov, s_lev, s_cov, fatal)
