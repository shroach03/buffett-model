"""CLI regression tests: briefs contain non-ASCII (×, −, ≥) and must write and print
cleanly on platforms whose default codepage is not UTF-8 (Windows)."""

import pytest

from buffett import analysis, report, scorecard, valuation
from buffett.analysis import analyze
from buffett.cli import main


def test_analyze_writes_utf8_with_lf_endings(tmp_path, capsys):
    assert main(["analyze", "ROL", "--out", str(tmp_path)]) == 0
    raw = (tmp_path / "ROL.md").read_bytes()
    text = raw.decode("utf-8")  # must be valid UTF-8, whatever the platform default
    assert "≥" in text and "×" in text
    assert b"\r\n" not in raw  # reproducible briefs: LF everywhere
    assert "Verdict" in capsys.readouterr().out


def test_screen_prints_multiplication_sign(capsys):
    assert main(["screen", "ROL"]) == 0
    assert "×" in capsys.readouterr().out


@pytest.mark.parametrize("cmd", [["analyze"], ["screen"], ["snapshot"]])
@pytest.mark.parametrize("bad", ["../../etc", "..", "A/B", r"A\B", "A..B", "", "TOOLONGTICKER"])
def test_rejects_path_like_tickers(cmd, bad, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as e:
        main([*cmd, bad, *(["--out", "out"] if cmd == ["analyze"] else [])])
    assert e.value.code == 2  # argparse usage error, before any I/O
    assert list(tmp_path.iterdir()) == []  # nothing written


def test_lowercase_ticker_is_normalised(capsys):
    assert main(["screen", "rol"]) == 0


def test_consistency_line_survives_missing_cash_conversion():
    r = analyze("ROL")
    r.cons.cash_conversion = None
    line = next(ln for ln in report.brief(r).splitlines() if ln.startswith("Consistency tests:"))
    assert line.endswith("cash conversion n/a")


def test_summary_table_shows_na_without_price(monkeypatch):
    monkeypatch.setattr(analysis, "load_prices", lambda: {"prices": {}})
    row = report.summary_table([analyze("ROL")]).splitlines()[-1].split(" | ")
    assert row[3] == "n/a" and row[8] == "n/a"  # P/OE, needed yr-10 multiple
    assert "0.0×" not in row


# 1e30: IRR not bracketed. CPRT at 1e-6: price below net cash/share (shorthand went complex).
@pytest.mark.parametrize("ticker, price", [("ROL", "1e30"), ("CPRT", "1e-6")])
def test_extreme_price_gives_brief_not_crash(ticker, price, capsys):
    assert main(["analyze", ticker, "--price", price]) == 0
    assert "Verdict" in capsys.readouterr().out


def test_unsolvable_irr_reports_na_and_warns(monkeypatch):
    def unsolvable(*a, **k):
        raise ValueError("IRR not bracketed")

    monkeypatch.setattr(valuation, "irr", unsolvable)
    r = analyze("ROL", price=1e9)
    assert r.expected_return_irr is None and r.ladder == {}
    md = report.brief(r)
    assert "IRR could not be solved" in md and "⚠ expected return not computable" in md
    assert "n/a" in report.summary_table([r])


@pytest.mark.parametrize("field,value", [("moat", 51), ("moat", -1), ("moat", True), ("management", 10.5)])
def test_judgment_rejects_out_of_range_scores(field, value):
    kwargs = {"moat": 10, "management": 5, "source": "test", "date": "2026-01-01", field: value}
    with pytest.raises(ValueError, match=field):
        scorecard.Judgment(**kwargs)


def test_judgment_file_missing_source_names_file_and_field(tmp_path):
    (tmp_path / "XYZ.json").write_text('{"moat": 10, "management": 5, "date": "2026-01-01"}', encoding="utf-8")
    with pytest.raises(ValueError, match=r"XYZ\.json.*source"):
        analysis.load_judgment("XYZ", tmp_path)


def test_judgment_file_out_of_range_names_file(tmp_path):
    (tmp_path / "XYZ.json").write_text(
        '{"moat": 51, "management": 5, "source": "s", "date": "2026-01-01"}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match=r"XYZ\.json.*moat"):
        analysis.load_judgment("XYZ", tmp_path)


@pytest.mark.parametrize("ticker", ["CPRT", "GGG", "ROL", "WAT", "WSO"])
def test_shipped_judgment_files_load(ticker):
    assert analysis.load_judgment(ticker) is not None


@pytest.mark.parametrize("bad", ["-5", "0", "nan", "inf", "abc"])
def test_cli_rejects_bad_price(bad, capsys):
    with pytest.raises(SystemExit) as e:
        main(["analyze", "ROL", "--price", bad])
    assert e.value.code == 2
    assert "invalid price" in capsys.readouterr().err


@pytest.mark.parametrize("bad", [-5.0, 0.0, float("nan"), float("inf"), float("-inf")])
def test_analyze_rejects_bad_price(bad):
    with pytest.raises(ValueError, match="price"):
        analyze("ROL", price=bad)


def test_snapshot_writes_to_out_dir_not_the_package(tmp_path, monkeypatch):
    from buffett import edgar

    monkeypatch.setattr(edgar, "fetch_companyfacts", lambda t: {"entityName": t, "facts": {}})
    out = tmp_path / "snaps"
    assert main(["snapshot", "ROL", "--out-dir", str(out)]) == 0
    assert (out / "ROL.json.gz").exists()
    monkeypatch.chdir(tmp_path)
    assert main(["snapshot", "GGG"]) == 0
    assert (tmp_path / "fixtures" / "GGG.json.gz").exists()  # default ./fixtures


def test_cache_lives_outside_the_package():
    from pathlib import Path

    from buffett import edgar

    pkg = Path(edgar.__file__).resolve().parent
    assert pkg not in edgar.CACHE.resolve().parents
