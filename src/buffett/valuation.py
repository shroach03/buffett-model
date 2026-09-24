"""Model §1, §10, §11, §12: expected return, DCF, reverse DCF and price ladder.

Growth comes only from reinvestment: g = b x ROIIC, and only the unretained
share (1 - b) of owner earnings is distributable. Nothing here assumes full
distribution *and* retained-earnings growth at once (the double count the
Model warns about).
"""
from __future__ import annotations

from dataclasses import dataclass, replace


def irr(cashflows: list[float], lo: float = -0.99, hi: float = 10.0, tol: float = 1e-10) -> float:
    """Internal rate of return by bisection. cashflows[0] is the (negative) price paid."""
    def npv(r):
        return sum(c / (1 + r) ** t for t, c in enumerate(cashflows))
    if npv(lo) * npv(hi) > 0:
        raise ValueError("IRR not bracketed")
    for _ in range(300):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def ten_year_irr(price: float, oeps: float, b: float, roiic: float, exit_multiple: float,
                 years: int = 10) -> float:
    """Model §11: buy at ``price``; owner earnings grow at g = b x ROIIC; the
    investor receives (1 - b) of each year's OE and sells at ``exit_multiple``
    times year-ten OE. Reproduces the Model's worked table exactly."""
    g = b * roiic
    flows = [-price]
    for t in range(1, years + 1):
        oe_t = oeps * (1 + g) ** t
        flows.append((1 - b) * oe_t + (exit_multiple * oe_t if t == years else 0.0))
    return irr(flows)


def expected_return_equation(price: float, oeps: float, b: float, roiic: float,
                             exit_multiple: float) -> float:
    """Model §1: R = b x ROIIC + (1-b) x OE/P + (M10/M0)^(1/10) - 1."""
    m0 = price / oeps
    return b * roiic + (1 - b) * oeps / price + (exit_multiple / m0) ** 0.1 - 1


def ladder_price(target: float, oeps: float, b: float, roiic: float, exit_multiple: float) -> float:
    """Price at which the ten-year IRR equals ``target`` (Model §12 watchlist tiers)."""
    lo, hi = oeps * 0.5, oeps * 500
    for _ in range(200):
        mid = (lo + hi) / 2
        if ten_year_irr(mid, oeps, b, roiic, exit_multiple) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


@dataclass(frozen=True)
class Case:
    name: str
    discount_rate: float
    oe_haircut: float        # 1.0 = today's normalized OE; 0.9 = margins partially decline
    g_start: float           # year-1 growth, fading linearly to g_terminal by year 10
    g_terminal: float
    roiic: float             # return on reinvestment during years 1-10
    roiic_terminal: float    # return on reinvestment after year 10
    hold_years: int = 0      # years g_start is held before the fade begins (bull: longer runway)


def project(oe0: float, case: Case, years: int = 10) -> dict:
    """Owner earnings path for one case. g_t is held at g_start for
    ``hold_years`` and then fades linearly to g_terminal by year ten; b_t = g_t / ROIIC is the share retained to fund that
    growth, and (1 - b_t) x OE_t is distributable. Terminal value at year ten
    is the Model's Gordon term OE_11 (1 - b_inf) / (r - g_inf)."""
    r = case.discount_rate
    oe = oe0 * case.oe_haircut
    path = []
    for t in range(1, years + 1):
        if t <= case.hold_years:
            g = case.g_start
        else:
            k, span = t - case.hold_years, years - case.hold_years
            g = case.g_start + (case.g_terminal - case.g_start) * k / span
        g = min(g, case.roiic)            # cannot grow faster than full reinvestment allows
        b = g / case.roiic if case.roiic > 0 else 1.0
        oe *= 1 + g
        path.append({"t": t, "g": g, "b": b, "oe": oe, "distributable": oe * (1 - b)})
    g_inf = case.g_terminal
    b_inf = min(g_inf / case.roiic_terminal, 1.0) if case.roiic_terminal > 0 else 1.0
    terminal = oe * (1 + g_inf) * (1 - b_inf) / (r - g_inf)
    return {"path": path, "terminal": terminal, "terminal_multiple": terminal / oe}


def dcf(oe0: float, shares: float, net_debt: float, case: Case, years: int = 10) -> dict:
    """Model §10:
    IV = sum_{t=1..10} OE_t (1-b_t)/(1+r)^t + OE_11 (1-b_inf) / ((r-g_inf)(1+r)^10)
    IVPS = (IV - net debt) / diluted shares."""
    r = case.discount_rate
    proj = project(oe0, case, years)
    pv = sum(p["distributable"] / (1 + r) ** p["t"] for p in proj["path"])
    pv_terminal = proj["terminal"] / (1 + r) ** years
    iv = pv + pv_terminal
    return {
        "case": case.name,
        "iv": iv,
        "ivps": (iv - net_debt) / shares,
        "terminal_share": pv_terminal / iv if iv else None,
        "implied_exit_multiple": proj["terminal_multiple"],
        "path": proj["path"],
        "assumptions": case,
    }


def case_irr(price: float, oeps0: float, net_debt_ps: float, case: Case,
             exit_multiple: float | None = None, years: int = 10) -> float:
    """Ten-year IRR from buying at ``price`` if the case plays out. The buyer
    also takes on net debt (or receives net cash), so the effective price is
    price + net debt per share. Exit at the case's own Gordon value unless an
    explicit year-ten multiple is given. At price == base-case IVPS this
    returns exactly the discount rate, so the 10% ladder rung equals base IV."""
    if price + net_debt_ps <= 0:
        return float("inf")   # paying less than net cash per share: return is unbounded
    proj = project(oeps0, case, years)
    flows = [-(price + net_debt_ps)] + [p["distributable"] for p in proj["path"]]
    terminal = proj["terminal"] if exit_multiple is None else exit_multiple * proj["path"][-1]["oe"]
    flows[-1] += terminal
    return irr(flows)


def case_ladder(target: float, oeps0: float, net_debt_ps: float, case: Case) -> float:
    """Price at which the base case returns ``target`` per year (Model §12)."""
    lo, hi = -net_debt_ps + 0.01 * oeps0, oeps0 * 500
    for _ in range(200):
        mid = (lo + hi) / 2
        if case_irr(mid, oeps0, net_debt_ps, case) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def required_exit_multiple(price: float, oeps0: float, net_debt_ps: float, case: Case, years: int = 10) -> float:
    """Reverse DCF, form 1: holding the case's growth path, the year-ten
    P/OE multiple the market must still pay for the buyer to earn the
    case's discount rate."""
    r = case.discount_rate
    proj = project(oeps0, case, years)
    pv = sum(p["distributable"] / (1 + r) ** p["t"] for p in proj["path"])
    needed_terminal = (price + net_debt_ps - pv) * (1 + r) ** years
    return needed_terminal / proj["path"][-1]["oe"]


def reverse_dcf(price: float, oe0: float, shares: float, net_debt: float, base: Case) -> float | None:
    """Reverse DCF, form 2: the starting growth rate (fading to the base
    terminal rate, at base-case ROIIC) at which intrinsic value equals the
    price. None if no growth rate up to min(40%, ROIIC) justifies it, i.e. the
    price needs a higher return on capital or a richer terminal multiple
    than the base case allows."""
    def value_at(g):
        return dcf(oe0, shares, net_debt, replace(base, g_start=g))["ivps"]
    lo, hi = -0.05, min(0.40, base.roiic)
    if value_at(hi) < price:
        return None
    if value_at(lo) > price:
        return lo
    for _ in range(100):
        mid = (lo + hi) / 2
        if value_at(mid) < price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
