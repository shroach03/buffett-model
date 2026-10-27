"""Unit tests for the XBRL cleaning rules, on small synthetic filings."""

import pytest

from buffett.consistency import compute as consistency
from buffett.normalize import build_financials
from buffett.owner_earnings import compute as owner_earnings


def fact(end, val, filed, start=None, form="10-K"):
    f = {"end": end, "val": val, "filed": filed, "form": form}
    if start:
        f["start"] = start
    return f


def annual(year, val, filed):
    return fact(f"{year}-12-31", val, filed, start=f"{year}-01-01")


def company(**tags):
    units = {}
    for tag, rows in tags.items():
        unit = "shares" if "Shares" in tag else "USD"
        units[tag] = {"units": {unit: rows}}
    return {"entityName": "TEST CO", "facts": {"us-gaap": units}}


def test_latest_filing_wins_and_restatement_logged():
    c = company(
        NetIncomeLoss=[annual(2020, 100, "2021-02-01"), annual(2020, 90, "2022-02-01"), annual(2021, 120, "2022-02-01")]
    )
    f = build_financials(c, "TST")
    assert f["net_income"] == [90, 120]
    assert len(f.restatements) == 1 and f.restatements[0].new == 90


def test_quarterly_durations_ignored():
    c = company(
        NetIncomeLoss=[annual(2021, 400, "2022-02-01"), fact("2021-12-31", 110, "2022-02-01", start="2021-10-01")]
    )
    assert build_financials(c, "TST")["net_income"] == [400]


def test_tag_switch_per_year():
    c = company(
        NetIncomeLoss=[annual(2017, 10, "2018-02-01"), annual(2018, 11, "2019-02-01")],
        SalesRevenueNet=[annual(2017, 100, "2018-02-01")],
        RevenueFromContractWithCustomerExcludingAssessedTax=[annual(2018, 110, "2019-02-01")],
    )
    f = build_financials(c, "TST")
    assert f["revenue"] == [100, 110]
    assert any("tag changed" in n for n in f.notes)


def test_missing_core_value_is_unknown_not_zero():
    c = company(
        NetIncomeLoss=[annual(2020, 10, "2021-02-01"), annual(2021, 11, "2022-02-01")],
        NetCashProvidedByUsedInOperatingActivities=[annual(2021, 15, "2022-02-01")],
    )
    assert build_financials(c, "TST")["cfo"] == [None, 15]


def test_zero_fill_only_outside_reported_span():
    ni = [annual(y, 10, f"{y + 1}-02-01") for y in (2018, 2019, 2020, 2021)]
    leases = [fact("2019-12-31", 50, "2020-02-01"), fact("2021-12-31", 60, "2022-02-01")]
    f = build_financials(company(NetIncomeLoss=ni, OperatingLeaseLiability=leases), "TST")
    # before first report -> 0 (pre-ASC 842); gap between reports -> unknown
    assert f["operating_leases"] == [0.0, 50, None, 60]


def test_stock_split_adjusts_older_years():
    ni = [annual(y, 10, f"{y + 1}-02-01") for y in (2018, 2019, 2020)]
    tag = "WeightedAverageNumberOfDilutedSharesOutstanding"
    shares = [
        annual(2018, 100e6, "2019-02-01"),
        annual(2019, 101e6, "2020-02-01"),  # last filing on the old basis
        annual(2019, 202e6, "2021-02-01"),  # 2-for-1 split, prior year restated
        annual(2020, 204e6, "2021-02-01"),
    ]
    f = build_financials(company(NetIncomeLoss=ni, **{tag: shares}), "TST")
    assert f["diluted_shares"] == [200e6, 202e6, 204e6]
    assert any("2-for-1" in n for n in f.notes)


def test_unscaled_thousands_repaired():
    ni = [annual(y, 10, f"{y + 1}-02-01") for y in (2019, 2020)]
    tag = "WeightedAverageNumberOfDilutedSharesOutstanding"
    shares = [annual(2019, 50_000, "2020-02-01"), annual(2019, 50e6, "2021-02-01"), annual(2020, 51e6, "2021-02-01")]
    f = build_financials(company(NetIncomeLoss=ni, **{tag: shares}), "TST")
    assert f["diluted_shares"] == [50e6, 51e6]


def test_52_53_week_year_ends_match():
    # Graco-style fiscal years end on the last Friday of December.
    ni = [
        fact("2024-12-27", 10, "2025-02-18", start="2023-12-30"),
        fact("2025-12-26", 11, "2026-02-17", start="2024-12-28"),
    ]
    eq = [fact("2024-12-27", 100, "2025-02-18"), fact("2025-12-26", 110, "2026-02-17")]
    f = build_financials(company(NetIncomeLoss=ni, StockholdersEquity=eq), "TST")
    assert f["equity"] == [100, 110]


def test_owner_earnings_and_sbc_treatment():
    years = (2020, 2021)
    c = company(
        NetIncomeLoss=[annual(2020, 90, "2021-02-01"), annual(2021, 100, "2022-02-01")],
        Revenues=[annual(2020, 1000, "2021-02-01"), annual(2021, 1100, "2022-02-01")],
        DepreciationDepletionAndAmortization=[annual(y, 30, f"{y + 1}-02-01") for y in years],
        PaymentsToAcquirePropertyPlantAndEquipment=[annual(y, 40, f"{y + 1}-02-01") for y in years],
        NetCashProvidedByUsedInOperatingActivities=[annual(y, 150, f"{y + 1}-02-01") for y in years],
        ShareBasedCompensation=[annual(y, 10, f"{y + 1}-02-01") for y in years],
        PropertyPlantAndEquipmentNet=[fact(f"{y}-12-31", 200, f"{y + 1}-02-01") for y in years],
        AssetsCurrent=[fact(f"{y}-12-31", 300, f"{y + 1}-02-01") for y in years],
        LiabilitiesCurrent=[fact(f"{y}-12-31", 200, f"{y + 1}-02-01") for y in years],
        CashAndCashEquivalentsAtCarryingValue=[fact(f"{y}-12-31", 50, f"{y + 1}-02-01") for y in years],
    )
    f = build_financials(c, "TST")
    oe = owner_earnings(f)
    assert oe.conservative_fcf[1] == 150 - 40 - 10  # CFO - capex - SBC
    # growth capex = PP&E/sales (0.19) x sales growth (100) = 19 -> capex - growth = 21,
    # but maintenance is floored at min(capex, D&A) = 30
    assert oe.maintenance_capex[1] == 30
    # operating WC = 300 - 50 - 200 = 50; median(50/1000, 50/1100) x 100 of sales growth
    assert oe.wc_requirement[1] == pytest.approx((50 / 1000 + 50 / 1100) / 2 * 100)
    assert oe.owner_earnings[1] == 100 + 30 - 30 - oe.wc_requirement[1]


def test_consistency_tests():
    oe = [10, 11, 12, 9, 13, 14, 15, 16, 17, 18]
    shares = [1.0] * 10
    c = consistency(oe, [o / s for o, s in zip(oe, shares, strict=True)], [12] * 10)
    assert c.positive_years == 10 and c.positive_test_pass
    assert c.oeps_cagr == (18 / 10) ** (1 / 9) - 1
    assert c.down_years == 1 and round(c.worst_one_year_decline, 4) == -0.25
    assert c.longest_recovery_years == 2  # peak 12 in yr 3, regained in yr 5
    assert round(c.cash_conversion, 4) == round(sum(oe) / 120, 4)
