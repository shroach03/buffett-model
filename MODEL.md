# The Model

"The Model" is the author's written quality-value investment framework. This document sets out the parts of it that the code implements, under the section numbers the code cites (`Model §N` in docstrings). Where the Model gives a principle and the code has to choose a number or a convention, the choice is labelled **operationalization**. That is this project's reading, kept in one place so it can be argued with and changed.

Sections §6–§8 of the Model are not cited by the code and are not reproduced here.

Defaults are named parameters in `analysis.Assumptions` (`hurdle` 10%, `min_mos` 20%, `roiic_cap` 30%, `g_cap` 12%, `peak_guard` 1.15, `window` 10 years).

## §1 Expected return

A business compounds only what it reinvests, at the return it earns on that reinvestment:

    g = b × ROIIC        (b = share of owner earnings retained)

The shorthand for an owner's annual return over ten years has three parts: growth, cash yield and re-rating.

    R ≈ b × ROIIC + (1 − b) × OE/P + (M₁₀ / M₀)^(1/10) − 1

M₀ is today's price / owner earnings and M₁₀ the multiple paid in year ten. Only the unretained share (1 − b) is distributable. Counting full distribution *and* retained-earnings growth at once is the double count the Model warns against.

The exact figure is the ten-year IRR (§11). The shorthand should land within about half a percentage point of it.

Code: `valuation.expected_return_equation`, `report._expected_return`.

## §2 Scorecard and decision rule

100 points: 70 for quality, 30 for price.

| Category | Points | Source |
|---|---:|---|
| Understandability & moat | 15 | judgment |
| Earnings quality & consistency | 15 | data (§4) |
| Returns on capital | 20 | data (§5) |
| Balance-sheet strength | 10 | data (§9) |
| Management & capital allocation | 10 | judgment |
| Valuation & expected return | 20 | data (§11) |
| Margin of safety | 10 | data (§10, §12) |

75 points are measured. The 25 judgment points come from a `Judgment` record (`src/buffett/data/judgment/TICKER.json`). It must name its source and date. Moat is an integer 0–15, management an integer 0–10. Without one the verdict is NEEDS JUDGMENT; the code never invents a score.

**Decision rule.** A stock is a **CANDIDATE** only if:

- quality ≥ 55 / 70,
- total ≥ 75 / 100,
- no fatal flaw,
- conservative expected return (base-case ten-year IRR) ≥ the hurdle (10%),
- margin of safety ≥ 20%.

If quality or a fatal flaw fails, it is **PASS**. If quality passes and price doesn't, it is **WAIT**. CANDIDATE means *study it*, never *buy it*.

**Operationalization: point bands.**

- *Earnings quality (15):*
  - positive owner-earnings years: 5 for ≥ 9/10, 3 for ≥ 8/10, pro-rated when fewer than 10 years exist;
  - OE/share CAGR: 4 / 3 / 2 / 1 at 10% / 6% / 3% / > 0%;
  - worst peak-to-trough: 3 / 2 / 1 at ≥ −15% / −30% / −50%;
  - cash conversion: 3 at ≥ 0.8×, 1 at ≥ 0.6×.
- *Returns on capital (20):*
  - median ROE: 5 / 3 at 15% / 10%;
  - median ROIC: 7 / 5 / 2 at 20% / 12% / 8%;
  - 5-year ROIIC: 5 / 4 / 2 at 15% / 12% / 8%, or 3 if ROIIC isn't meaningful but NOPAT grew;
  - worst-year ROIC: 3 / 1 at 10% / 6%.
- *Balance sheet (10):* see §9.
- *Valuation (20):* 20 / 17 / 14 / 9 / 5 / 2 at a base-case IRR of 15% / 12% / 10% / 8% / 6% / 4%.
- *Margin of safety (10):* 10 / 8 / 5 / 3 / 1 at a discount to base-case value of 30% / 20% / 10% / 0% / −15%.

Unknown inputs score 0. A data gap never earns the points of a good number.

Code: `scorecard.py`, `analysis._score`, `report._scorecard`.

## §3 Owner earnings

Cash flow is measured as owner earnings, not reported EPS.

    OE = net income + D&A + non-cash impairments
         − maintenance capex − working capital needed for growth

Stock-based compensation is a real cost. Net income already expenses it, so OE keeps it as a cost. The cross-check, conservative FCF = CFO − total capex − SBC, deducts it again because CFO adds it back.

**Operationalization.**

- **Maintenance capex** isn't reported, so it is estimated:
  - growth capex = (trailing PP&E / sales) × max(sales increase, 0);
  - maintenance = max(capex − growth capex, min(capex, D&A)), capped at capex.

  A business is never assumed to maintain its assets for less than its D&A charge.
- **Working capital needed for growth** = median of operating working capital / sales over five years × the sales increase, floored at 0. The median keeps one noisy year-end from swinging owner earnings.
- **Normalized owner earnings** (the valuation starting point) is the latest year. If that year is more than 115% of the three-year mean, the mean is used instead, so a peak year isn't capitalized.

Code: `owner_earnings.py`, `analysis.normalized`.

## §4 Ten-year consistency

Four tests on the last ten years of owner earnings:

1. **Positive years:** how many of the ten years had positive OE.
2. **Growth:** OE/share CAGR, (OEPS₁₀ / OEPS₁)^(1/9) − 1.
3. **Drawdowns:** number of down years, the worst one-year decline, the worst peak-to-trough fall, and the longest time to regain a prior peak.
4. **Cash conversion:** the sum of OE over the sum of net income. It tests whether reported profit turns into cash.

Years with missing inputs are left unknown, not estimated. The report warns when fewer than ten years are computable.

Code: `consistency.py`, `report._ten_year`.

## §5 Returns on capital

    ROE    = net income / average common equity
    NOPAT  = EBIT × (1 − normalized tax rate)
    IC     = debt + equity − excess cash
    ROIC   = NOPAT / average invested capital
    ROIIC₅ = (NOPAT_t − NOPAT_t−5) / (IC_t − IC_t−5)

ROIIC, the return on *incremental* capital, is the most important of these. It is what §1's `g = b × ROIIC` runs on.

**Operationalization.**

- **Tax rate:** total tax / total pretax income over five years, clamped to 10–35%.
- **Excess cash:** cash + short-term investments − 2% of revenue.
- **Operating leases:** left out of invested capital, because their cost is already inside EBIT and they reached balance sheets only in 2019. They are included in §9.
- **Negative denominators:** ratios over non-positive equity or invested capital are "not meaningful", not huge or negative percentages.

Code: `returns.py`.

## §9 Debt under adverse conditions

Debt is tested against bad years, not average ones.

    Net debt          = total debt + operating leases − excess cash
    Net debt / OE     < ~2× normalized owner earnings
    Interest coverage = EBIT / interest  > 6×

**Stress test.** The company's own worst one-year percentage fall in EBIT and in owner earnings over ten years is applied to today's figures. Using the worst *level* instead would compare today's debt with a decade-old trough from a much smaller business.

**Fatal flaw (operationalization):** stressed net debt above 3× stressed OE, or stressed coverage below 3×. It stands for "leverage that can turn a temporary problem into permanent loss".

**Points (10):**

- leverage: 5 for net cash, else 4 / 3 / 1 at ≤ 1× / 2× / 3× OE;
- coverage: 5 if there is no interest expense, else 5 / 4 / 2 at ≥ 12× / 6× / 3×.

Unknown debt or interest scores 0, never the points of "no debt" or "no interest". The report then warns that the stress test is incomplete.

XBRL company facts can't show pension deficits, supplier financing, factored receivables, guarantees, litigation or maturity walls. Those belong to the judgment layer.

Code: `balance_sheet.py`, `scorecard.balance_sheet`.

## §10 Intrinsic value (DCF)

    IV   = Σ_{t=1..10} OE_t (1 − b_t) / (1 + r)^t  +  OE₁₁ (1 − b_∞) / ((r − g_∞)(1 + r)^10)
    IVPS = (IV − net debt) / diluted shares

Growth starts at g_start and fades linearly to the terminal rate g_∞ by year ten. Each year retains b_t = g_t / ROIIC to fund that growth, and only (1 − b_t) is distributable. The terminal value is a Gordon term and requires r > g_∞. Net debt here excludes leases, because lease cost is already inside OE.

Three cases (operationalization):

| | r | OE haircut | Start g | Terminal g | ROIIC (yrs 1–10 / after) |
|---|---|---|---|---|---|
| Bear | hurdle + 2% | 0.90 | min(½ base g, bear ROIIC) | 1.5% | 0.6 × base / hurdle + 2% |
| Base | hurdle | 1.00 | min(b_hist × ROIIC_base, 12%) | 2.5% | ROIIC_base / ROIIC_base |
| Bull | hurdle | 1.00 | min(b_hist × max(hist, base), 15%), held 5 yrs | 3.0% | max(hist, base) |

ROIIC_base = min(5-year ROIIC, median ROIC, 30%). If incremental returns are near zero (≤ 2%), the business is valued as no-growth. If owner earnings, shares, ROIIC or debt are unknown, no DCF is produced.

Code: `valuation.project`, `valuation.dcf`, `analysis._build_cases`, `report._intrinsic_value`.

## §11 Ten-year IRR and the worked example

The conservative expected return is the ten-year IRR of buying at today's price, plus net debt per share, if the base case plays out. The investor receives each year's distributable OE and, in year ten, the case's own terminal value. Buying at exactly base-case IVPS therefore returns exactly the hurdle.

The Model's worked example: OE/share $6.50, retention 60%, ROIIC 12% (so g = 7.2%), exit at 15× year-ten OE:

| Price | P/OE | OE yield | Ten-year IRR |
|---:|---:|---:|---:|
| $80 | 12.3× | 8.1% | 12.5% |
| $100 | 15.4× | 6.5% | 9.7% |
| $130 | 20.0× | 5.0% | 6.6% |

`tests/test_model_math.py` reproduces this table exactly, and it fixed the exit convention.

**Reverse DCF** asks what today's price assumes, in two forms:

1. the year-ten P/OE the market must still pay for the buyer to earn the hurdle, holding the base growth path;
2. the starting growth rate, at base-case ROIIC, at which intrinsic value equals the price.

The brief also reports the IRR with no re-rating (exit at today's multiple).

Code: `valuation.ten_year_irr`, `valuation.case_irr`, `valuation.required_exit_multiple`, `valuation.reverse_dcf`.

## §12 Margin of safety and price ladder

    Margin of safety = 1 − price / base-case IVPS     (required: ≥ 20%)

The price ladder gives the price at which the base case returns 8%, 10%, 12% and 15% a year. These are the watchlist tiers. The hurdle rung is always included and equals base-case intrinsic value. The ladder turns a WAIT into a concrete question: at what price would this become a CANDIDATE?

Code: `valuation.case_ladder`, `analysis._price_outputs`, `report._intrinsic_value`.
