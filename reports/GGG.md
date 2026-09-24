# GGG · Graco Inc.

**Verdict: WAIT**, quality passes; expected return 1.6% < 10% hurdle; margin of safety -84.8% < 20%; total 66/100 < 75  
Latest annual data: FY2025 10-K (period ending 2025-12-26) · Price: $76.28 (2026-09-16)

## Scorecard

| Category | Points | Max | Basis |
|---|---:|---:|---|
| Understandability & moat | 13 | 15 | judgment: Opportunity brief of 2026-08-03 (LLM-assisted chat session, reviewed by the user; not independently verified). Replace with your own read. |
| Earnings quality & consistency | 15 | 15 | 10/10 positive OE yrs; OEPS CAGR 13.7%; worst drawdown -12.3%; conversion 0.92x |
| Returns on capital | 20 | 20 | median ROE 27.2%; median ROIC 32.2%; 5y ROIIC 19.6%; worst ROIC 10.8% |
| Balance-sheet strength | 10 | 10 | net debt incl. leases -551M = -1.15x OE; coverage 216x |
| Management & allocation | 8 | 10 | judgment (see notes); share count -0.1%/yr over 10y |
| **Quality subtotal** (≥ 55) | **66** | 70 | |
| Valuation & expected return | 0 | 20 | conservative 10y IRR 1.6% |
| Margin of safety | 0 | 10 | discount to base-case IV -84.8% |
| **Total** (≥ 75) | **66** | 100 | |

**Fatal flaws:** none detected in the data

**Judgment notes (2026-08-03):** Moat: premium brand + installed-base parts in fluid-handling equipment. Management: disciplined, opportunistic buybacks, orderly CFO succession.

## Expected return

- **Base-case 10-year IRR: 1.6%** vs 10% hurdle. Growth starts at g = b × ROIIC = 40.5% × 19.6% = 7.9% and fades to 2.5%; exit at the base case's own value, 11.9× OE.
- Model shorthand: R ≈ b×ROIIC + (1−b)×OE/P + Δmultiple = 40.5%×19.6% + 59.5%×3.9% + (11.9/25.8)^(1/10)−1 = **2.8%** (holds year-one growth for all ten years, so it differs from the IRR).
- If the market keeps paying today's 25.8× owner earnings in year ten: 8.1%.
- Reverse DCF: to earn 10% from here, the market must pay **31.8× owner earnings in year ten** (base case: 11.9×). Holding the base terminal assumptions instead, no starting growth rate at the base-case ROIIC of 19.6% justifies today's price.

## Intrinsic value (Model §10 DCF)

Normalized owner earnings 477M = $2.82/share; net debt excl. leases -578M; 169.2M diluted shares.

| Case | r | Start g | Terminal g | ROIIC | IV/share | Terminal share | Exit multiple |
|---|---:|---:|---:|---:|---:|---:|---:|
| bear | 12% | 4.0% | 1.5% | 11.7% | $24.95 | 42% | 8.5× |
| base | 10% | 7.9% | 2.5% | 19.6% | $41.27 | 55% | 11.9× |
| bull | 10% | 7.9% | 3.0% | 19.6% | $45.02 | 61% | 12.5× |

Margin of safety vs base case: **-85%** (Model wants 20–30%).

**Price ladder** (base-case 10-year return): 8% → $47.27 · 10% → $41.27 · 12% → $36.27 · 15% → $30.25

## Ten-year record (USD millions)

| FY | Revenue | Net income | Owner earnings | OE/share | CFO−capex−SBC | ROIC | Diluted sh (M) |
|---|---|---|---|---|---|---|---|
| FY2016 | 1,329 | 41 | 178 | 1.04 | 213 | 11% | 170.9 |
| FY2017 | 1,475 | 252 | 228 | 1.31 | 274 | 36% | 174.3 |
| FY2018 | 1,653 | 341 | 305 | 1.76 | 289 | 40% | 173.2 |
| FY2019 | 1,646 | 344 | 265 | 1.54 | 264 | 37% | 171.6 |
| FY2020 | 1,650 | 330 | 314 | 1.83 | 298 | 31% | 172.0 |
| FY2021 | 1,988 | 440 | 368 | 2.11 | 298 | 37% | 174.5 |
| FY2022 | 2,144 | 461 | 331 | 1.91 | 152 | 33% | 172.9 |
| FY2023 | 2,196 | 507 | 407 | 2.36 | 436 | 32% | 172.2 |
| FY2024 | 2,113 | 486 | 466 | 2.70 | 483 | 26% | 172.4 |
| FY2025 | 2,237 | 522 | 559 | 3.31 | 604 | 26% | 169.2 |

Consistency tests: 10/10 positive OE years · OEPS CAGR 13.7% · 2 down years, worst -12.3% · longest recovery 2y · cash conversion 0.92×

## Balance sheet (latest year)

Debt 2M + operating leases 27M − excess cash 579M = net debt **-551M** (-1.15× OE; stressed -1.33×). Coverage 216× (stressed 190×). Not testable from XBRL facts: pension deficits, supplier financing, guarantees, litigation, maturity schedule.

## Data provenance

Source: SEC XBRL company facts, 10-K and 10-K/A filings only. 10 restated values detected (latest filing used). Normalization notes:

- revenue: tag changed over time -> Revenues | SalesRevenueNet
- pretax_income: tag changed over time -> IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments
- net_income: tag changed over time -> NetIncomeLoss | NetIncomeLossAvailableToCommonStockholdersBasic
- interest_expense: tag changed over time -> InterestExpense | InterestExpenseNonoperating
- impairments: tag changed over time -> AssetImpairmentCharges | GoodwillImpairmentLoss | ImpairmentOfLongLivedAssetsHeldForUse
- WeightedAverageNumberOfDilutedSharesOutstanding 2013-12-27: value filed 2015-02-17 was off by 1000x (unscaled thousands); rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding 2014-12-26: value filed 2015-02-17 was off by 1000x (unscaled thousands); rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding 2012-12-28: value off by 1000x vs neighbouring years; rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding: 3-for-1 stock split detected after filing of 2017-02-21; earlier values adjusted
- equity: tag changed over time -> StockholdersEquity | StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest
- long_term_debt: tag changed over time -> LongTermDebtCurrent | LongTermDebtNoncurrent | LongTermDebtNoncurrent+LongTermDebtCurrent
- operating_leases: not reported for 2013-12, 2014-12, 2015-12, 2016-12, 2017-12; treated as 0
- operating_leases: tag changed over time -> OperatingLeaseLiability | OperatingLeaseLiabilityCurrent+OperatingLeaseLiabilityNoncurrent

*Analysis for one individual's own decision, not investment advice. A CANDIDATE is a prompt to study, never an instruction to buy.*
