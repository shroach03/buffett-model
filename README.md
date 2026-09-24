# buffett-model

[![tests](https://github.com/shroach03/buffett-model/actions/workflows/ci.yml/badge.svg)](https://github.com/shroach03/buffett-model/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Give it a ticker, get a reproducible buy / wait / pass verdict, computed from the SEC's own filings.** A deterministic implementation of a Buffett-style quality-value investment framework, running on SEC XBRL financial data.

```text
$ buffett screen ROL WAT
| Ticker | Price   | P/OE  | Base IV | Base IRR | Quality | Total | Verdict |
| ROL    | $33.53  | 27.0× | $19.45  |     3.3% |      64 |    64 | WAIT    |
| WAT    | $418.64 | 36.9× | $73.73  |    -8.6% |      46 |    46 | PASS    |
```

*(Trimmed for the README. The real table has more columns.)*

The framework started as a set of prompts for an LLM. The LLM did all the arithmetic in chat, from numbers it found by web search. That left no way to reproduce a score or check a valuation. This repo moves every calculation into tested code and keeps the LLM (or a human) only for the two judgment categories that data can't measure: moat and management.

> Analysis tooling for one person's own decisions. Not investment advice.

### What is "the Model"?

The README and the code refer to "the Model" throughout. It is the author's own written investment framework, and this repo is its executable form. In short:

- **Owner earnings** as the cash-flow measure, not reported EPS: net income + D&A + non-cash impairments − estimated maintenance capex − the working capital needed to support growth. Stock-based compensation counts as a real cost.
- **A 100-point scorecard.** 70 points for quality: moat, earnings consistency, returns on capital (ROE, ROIC, 5-year ROIIC), balance sheet and management. The other 30 are valuation and margin of safety. 75 points are measured from data and 25 come from judgment.
- **A decision rule.** A stock is a CANDIDATE only if quality ≥ 55, the conservative 10-year expected return clears a 10% hurdle, the margin of safety is ≥ 20% and the total is ≥ 75. Otherwise it is WAIT or PASS.
- **A price ladder and reverse DCF.** They answer "what price earns 10%?" and "what does today's price assume?".

The section numbers cited in the code (§1, §10, §11, §12) refer to that document.

## What it does

```
SEC companyfacts JSON ──► normalize.py ──► owner_earnings / returns / consistency / balance_sheet
  (10 yrs of XBRL)        one clean row          │
                          per fiscal year        ▼
                                           valuation.py  (bear/base/bull DCF, reverse DCF, IRR, ladder)
                                                 │
            judgment/TICKER.json ───────────►  scorecard.py  ──► verdict + Markdown brief
            (moat, management,                  75 pts measured
             fatal flaws, with a source)        25 pts judgment
```

```bash
pip install -e ".[dev]"
pytest -q                                   # 48 tests, offline
buffett screen CPRT GGG ROL WAT WSO         # summary table
buffett analyze ROL --out reports           # full brief
export SEC_USER_AGENT="Your Name you@example.com"
buffett analyze MSFT --live --price 450     # live SEC data
```

## Results on the five test companies

Snapshot of SEC data retrieved 2026-09-24. Prices are Sep 16, 2026 closes. Full briefs are in [`reports/`](reports/).

| Ticker | P/OE | Base IV | Base 10y IRR | IRR if today's multiple holds | Year-10 multiple needed for 10% | Quality | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| CPRT | 20.8× | $21.92 | 5.2% | 10.1% | 20.6× | 64 | WAIT |
| GGG | 25.8× | $41.27 | 1.6% | 8.1% | 31.8× | 66 | WAIT |
| ROL | 27.0× | $19.45 | 3.3% | 9.8% | 27.6× | 64 | WAIT |
| WAT | 36.9× | $73.73 | −8.6% | 4.4% | 64.2× | 46 | PASS |
| WSO | 22.6× | $186.70 | 3.5% | 8.6% | 26.5× | 61 | WAIT |

WAT's price-based columns aren't meaningful: they compare a post-merger share price with pre-merger per-share owner earnings (see Limitations).

These are four excellent businesses (median ROIC 23–32%, 10 of 10 years of positive owner earnings) at prices that only work if the market still pays 20–30× owner earnings in 2036. The Model's own DCF (terminal growth 2–3%) implies about 12×. The reverse-DCF column states that gap directly.

### Code vs. the original LLM-in-chat analysis

The same five companies were scored in chat on Aug 3, 2026.

| Ticker | Chat verdict (total) | Code verdict (total) | What differed |
|---|---|---|---|
| CPRT | WAIT (79) | WAIT (66) | Chat put R at 10% by assuming "~0" multiple change. The code shows that assumption is the whole return: with a 20.8× multiple held, R = 10.1%; at the Model's base terminal value, 5.2%. |
| GGG | WAIT (70) | WAIT (66) | Agree. |
| ROL | WAIT (71) | WAIT (64) | Agree on verdict. Code's 10% ladder rung is lower ($19 vs $30) for the same multiple reason. |
| WAT | PASS (51) | PASS (46) | Same verdict, different evidence. See Waters below. |
| WSO | PASS (61) | WAIT (61) | Chat failed the quality gate on the 2022→25 earnings decline. The code's 5-year ROIIC window (FY2020→25) includes the 2021–22 pricing windfall and scores returns 20/20. The window choice changes the verdict. That's a real sensitivity worth knowing, and chat never exposed it. |

## The data engineering

The SEC publishes every tagged number from every filing as JSON (no scraping involved). The work is in cleaning it. Every problem below turned up in these five companies and has a test:

| Problem | Example found | Handling |
|---|---|---|
| **Stock splits.** A 10-K restates only the prior two years, so older years stay on the old basis. | Rollins' three 3-for-2 splits (2015, 2018, 2020). Graco's 3-for-1 (2017). Copart's share count jumps 4× between its FY2022 and FY2023 10-Ks. | A split is detected when the same period is re-reported at a split-like ratio. Every value filed before the split gets that factor applied. A test asserts no year-over-year share jump over 25%. |
| **Unscaled values** | Copart, Graco and Rollins 2014–15 filings tagged share counts in thousands without the scale (129,781 instead of 129,781,000). | Values ~1000× off from another filing or neighbouring years are rescaled, and the fix is logged. |
| **Tag drift** | Revenue moves from `SalesRevenueNet` to `RevenueFromContract…` (ASC 606). Rollins' D&A tag changes in 2019. Copart's cash tag changes in 2020. | Fallback chains resolved per fiscal year, with the winning tag logged for every year. |
| **Missing tags** | Waters tagged capex with a company-specific extension before 2023. The companyfacts API doesn't carry extensions. | Left **unknown**. Waters gets 3 years of owner earnings, not 10, and its score drops. Nothing is estimated silently. |
| **Absence ≠ zero** | Leases absent before 2019 (not on the balance sheet yet); debt absent after repayment; one missing Watsco lease year. | Missing before the first or after the last report → 0. A gap between reported years → unknown. |
| **Restatements** | Rollins restated 2020–21 net income, D&A and equity. | Latest filing wins, and every restatement over 0.5% is logged. |
| **Duplicates / durations** | Each period appears in up to 3 filings; Copart's 10-Ks include quarterly figures. | Keyed on actual period dates, not the filing's `fy` label; only 350–380-day durations count as annual. |
| **Fiscal calendars** | Copart's year ends Jul 31. Graco's 52/53-week year ends on the last Friday of December. | Periods are matched to each company's own year-end dates with ±6 days tolerance. |

## Design decisions

- **Unknown propagates.** A missing input makes the downstream number `None`, never a guess. That's the Model's own rule: a silent gap becomes a wider margin of safety.
- **One projection, three uses.** The DCF, the expected-return IRR and the price ladder share a single owner-earnings projection. By construction, the 10% ladder rung equals base-case intrinsic value (a test enforces it). The Model's shorthand `R ≈ b×ROIIC + (1−b)×OE/P + Δmultiple` is shown alongside.
- **Growth only from reinvestment.** `g = b × ROIIC`, and only `(1−b)` of owner earnings is distributable, so growth is never counted twice.
- **SBC is a cost.** Deducted from CFO-based free cash flow; already expensed in the net-income-based owner earnings.
- **Judgment is an input, not a hidden score.** Without a `judgment/TICKER.json`, the verdict is `NEEDS JUDGMENT` (or `PASS` if the measurable part already fails). It is never a made-up CANDIDATE. The bundled judgment files come from the Aug 3 chat briefs and are labeled that way.
- **Assumptions are named.** Every point band, cap and threshold that isn't a Model default is in `Assumptions` or `scorecard.py`, so each one can be argued with and changed.
- **Tests use the Model's own example.** §11's table ($80 → 12.5%, $100 → 9.7%, $130 → 6.6% IRR) reproduces exactly, and it pinned down which exit convention the Model uses.

## Limitations (read before trusting a number)

- **Annual 10-K data only.** Anything after the last 10-K is invisible to the code. Waters' Feb 2026 merger with BD's biosciences unit (≈$4B of new debt, share count nearly doubled) is in the judgment file as a fatal flaw, not in the numbers. Copart's FY2026 10-K was not yet filed at snapshot time.
- **Maintenance capex is estimated** (the sales-intensity method, floored at D&A). It misreads growth spending that doesn't track sales, e.g. Copart's land purchases in FY2020 depress that year's owner earnings.
- **One-off gains aren't removed.** Impairments are added back as non-cash; gains on sale are not stripped out.
- **Balance-sheet items XBRL can't see**: pension detail, supplier financing, guarantees, litigation and maturity walls belong in the judgment layer.
- **Fatal-flaw leverage threshold** (stressed net debt > 3× OE or coverage < 3×) is this project's reading of the Model, not the Model's text.
- **Point bands** within each scorecard category are an operationalization. WSO shows that the ROIIC window alone can move a verdict.
- **Live fetch path** (`--live`) isn't exercised in CI. It shares the schema and normalizer with the bundled snapshots.

## Layout

```
src/buffett/
  edgar.py           SEC API client (User-Agent, rate limit, daily cache) + snapshot loader
  concepts.py        Model inputs → XBRL tag fallback chains
  normalize.py       duplicates, restatements, splits, scale errors, fiscal calendars
  owner_earnings.py  conservative FCF and Buffett owner earnings
  returns.py         ROE, ROIC, 5-year ROIIC, reinvestment rate
  consistency.py     the four ten-year tests
  balance_sheet.py   leverage and coverage, including stressed
  valuation.py       §11 IRR, DCF cases, reverse DCF, ladder
  scorecard.py       100-point scorecard and decision rule
  analysis.py        pipeline + named assumptions
  report.py / cli.py Markdown briefs and command line
data/fixtures/       gzipped SEC companyfacts snapshots (10-K facts) for offline tests
data/judgment/       moat / management / fatal-flaw inputs, each with a source and date
data/prices.json     dated price snapshot
reports/             generated briefs
tests/               Model-math, normalization and five-company integration tests
```

## Reproducibility

Every result in this README can be regenerated offline from the bundled snapshots: `buffett analyze TICKER --out reports` reproduces the files in [`reports/`](reports/) byte for byte. Briefs are written as UTF-8 with LF line endings on every platform, and a CLI test guards this.

## Roadmap

1. An LLM layer that reads 10-K text and emits `judgment/*.json` with a structured schema and citations.
2. Evals for that layer: score variance across repeated runs, and verdict distribution across batches (to catch grade inflation).
3. A hand-entered override file for extension-tagged items (e.g. Waters' capex), with citations.
4. Quarterly (10-Q) updates between annual reports.

## License

[MIT](LICENSE). SEC filing data is public. The bundled snapshots are unmodified `companyfacts` responses from the SEC's EDGAR API.
