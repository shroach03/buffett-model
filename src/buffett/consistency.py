"""Model §4: the four ten-year consistency tests."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise


@dataclass
class Consistency:
    years_available: int
    positive_years: int
    oeps_cagr: float | None
    down_years: int
    worst_one_year_decline: float | None
    worst_peak_to_trough: float | None
    longest_recovery_years: int
    cash_conversion: float | None
    positive_test_pass: bool
    conversion_test_pass: bool | None


def compute(
    oe: list[float | None], oeps: list[float | None], net_income: list[float | None], window: int = 10
) -> Consistency:
    oe, oeps, ni = oe[-window:], oeps[-window:], net_income[-window:]
    avail = [x for x in oe if x is not None]
    positive = sum(1 for x in avail if x > 0)

    cagr = None
    idx = [i for i, x in enumerate(oeps) if x is not None]
    if len(idx) >= 2:
        first, last = oeps[idx[0]], oeps[idx[-1]]
        span = idx[-1] - idx[0]  # (OEPS_10 / OEPS_1)^(1/9) - 1 for a full window
        if first is not None and last is not None and first > 0 and last > 0:
            cagr = (last / first) ** (1 / span) - 1

    down, worst1 = 0, None
    for a, b in pairwise(oeps):
        if a is None or b is None or a <= 0:
            continue
        chg = b / a - 1
        if chg < 0:
            down += 1
            worst1 = chg if worst1 is None else min(worst1, chg)

    peak, worst_dd, longest, below_since = None, None, 0, None
    for i, x in enumerate(oeps):
        if x is None:
            continue
        if peak is None or x >= peak:
            if below_since is not None:
                longest = max(longest, i - below_since)
            peak, below_since = x, None
        else:
            if below_since is None:
                below_since = i - 1
            if peak > 0:
                dd = x / peak - 1
                worst_dd = dd if worst_dd is None else min(worst_dd, dd)
    if below_since is not None:  # never regained the peak inside the window
        longest = max(longest, len(oeps) - 1 - below_since)

    pairs = [(o, n) for o, n in zip(oe, ni, strict=True) if o is not None and n is not None]
    conv = sum(o for o, _ in pairs) / sum(n for _, n in pairs) if pairs and sum(n for _, n in pairs) > 0 else None

    return Consistency(
        years_available=len(avail),
        positive_years=positive,
        oeps_cagr=cagr,
        down_years=down,
        worst_one_year_decline=worst1,
        worst_peak_to_trough=worst_dd,
        longest_recovery_years=longest,
        cash_conversion=conv,
        positive_test_pass=len(avail) >= 10 and positive >= 9,
        conversion_test_pass=None if conv is None else conv >= 0.8,
    )
