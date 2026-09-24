"""Integration tests on the five bundled SEC snapshots.

Ground truth: figures from each company's FY2024 annual report / earnings
release (checked against the reported numbers, not against this pipeline's
output). Tolerance 0.5%.
"""
import pytest

from buffett import edgar
from buffett.analysis import analyze
from buffett.normalize import build_financials

TICKERS = ["CPRT", "GGG", "ROL", "WAT", "WSO"]

# (revenue, net income attributable to common) in USD millions, fiscal 2024
FY2024 = {
    "CPRT": (4_236.9, 1_363.5),   # FY ended 2024-07-31
    "GGG": (2_113.3, 486.1),
    "ROL": (3_388.7, 466.4),
    "WAT": (2_958.4, 637.8),
    "WSO": (7_618.3, 536.3),      # attributable to Watsco (excl. noncontrolling interest)
}


@pytest.fixture(scope="module", params=TICKERS)
def fin(request):
    return build_financials(edgar.load_snapshot(request.param), request.param)


@pytest.mark.parametrize("ticker", TICKERS)
def test_fy2024_matches_reported(ticker):
    f = build_financials(edgar.load_snapshot(ticker), ticker)
    i = [lab for lab in f.fy_labels()].index("FY2024")
    rev, ni = FY2024[ticker]
    assert f["revenue"][i] / 1e6 == pytest.approx(rev, rel=0.005)
    assert f["net_income"][i] / 1e6 == pytest.approx(ni, rel=0.005)


def test_ten_years_of_core_inputs(fin):
    core = ["revenue", "net_income", "da", "cfo", "diluted_shares", "equity"]
    for c in core:
        missing = [y for y, v in zip(fin.years[-10:], fin[c][-10:]) if v is None]
        # WSO's FY2022 diluted share count is absent from its XBRL: allowed, and reported as unknown.
        assert len(missing) <= 1, f"{fin.ticker} {c} missing {missing}"


def test_share_counts_have_no_split_jumps(fin):
    s = [x for x in fin["diluted_shares"] if x]
    for a, b in zip(s, s[1:]):
        assert 0.8 < b / a < 1.25, f"{fin.ticker}: unadjusted split or scale error ({a:,.0f} -> {b:,.0f})"


def test_known_splits_detected():
    notes = {t: " ".join(build_financials(edgar.load_snapshot(t), t).notes) for t in ("GGG", "ROL")}
    assert "3-for-1" in notes["GGG"]                       # Graco, December 2017
    assert notes["ROL"].count("1.5-for-1") == 3            # Rollins 3-for-2 splits: 2015, 2018, 2020


def test_waters_capex_gap_is_unknown_not_zero():
    # Waters tagged capex with a company-specific extension before 2023, which the
    # companyfacts API does not include. The pipeline must not invent those years.
    f = build_financials(edgar.load_snapshot("WAT"), "WAT")
    labels = f.fy_labels()
    assert f["capex"][labels.index("FY2020")] is None
    r = analyze("WAT", judgment=False)
    assert r.cons.years_available < 10 and r.warnings


@pytest.mark.parametrize("ticker", TICKERS)
def test_pipeline_runs_and_is_internally_consistent(ticker):
    r = analyze(ticker, price=100.0)
    base = next(c for c in r.cases if c["case"] == "base")
    assert r.ladder[0.10] == pytest.approx(base["ivps"], rel=1e-4)
    bear = next(c for c in r.cases if c["case"] == "bear")
    assert bear["ivps"] < base["ivps"]
    assert r.decision["verdict"] in {"PASS", "WAIT", "CANDIDATE", "NEEDS JUDGMENT"}


def test_no_judgment_means_no_candidate():
    for t in TICKERS:
        assert analyze(t, price=1.0, judgment=False).decision["verdict"] in {"PASS", "NEEDS JUDGMENT"}
