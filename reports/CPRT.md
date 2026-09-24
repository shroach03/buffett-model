# CPRT · Copart, Inc.

**Verdict: WAIT**, quality passes; expected return 5.2% < 10% hurdle; margin of safety -40.6% < 20%; total 66/100 < 75  
Latest annual data: FY2025 10-K (period ending 2025-07-31) · Price: $30.82 (2026-09-16)

## Scorecard

| Category | Points | Max | Basis |
|---|---:|---:|---|
| Understandability & moat | 13 | 15 | judgment: Opportunity brief of 2026-08-03 (LLM-assisted chat session, reviewed by the user; not independently verified). Replace with your own read. |
| Earnings quality & consistency | 14 | 15 | 10/10 positive OE yrs; OEPS CAGR 22.2%; worst drawdown -28.4%; conversion 0.87x |
| Returns on capital | 20 | 20 | median ROE 31.1%; median ROIC 28.7%; 5y ROIIC 17.6%; worst ROIC 21.8% |
| Balance-sheet strength | 10 | 10 | net debt incl. leases -2,587M = -1.96x OE; coverage 840x |
| Management & allocation | 7 | 10 | judgment (see notes); share count 0.0%/yr over 10y |
| **Quality subtotal** (≥ 55) | **64** | 70 | |
| Valuation & expected return | 2 | 20 | conservative 10y IRR 5.2% |
| Margin of safety | 0 | 10 | discount to base-case IV -40.6% |
| **Total** (≥ 75) | **66** | 100 | |

**Fatal flaws:** none detected in the data

**Judgment notes (2026-08-03):** Moat: owned salvage-yard land near metros + global buyer network. Management: CEO turnover (founder back Jul 2026); large buyback near lows. Open question: is the US volume decline cyclical (underinsurance) or share loss to IAA? Subsequent event: ~$1.9B ACV Auctions acquisition announced Sep 2026.

## Expected return

- **Base-case 10-year IRR: 5.2%** vs 10% hurdle. Growth starts at g = b × ROIIC = 68.1% × 17.6% = 12.0% and fades to 2.5%; exit at the base case's own value, 11.7× OE.
- Model shorthand: R ≈ b×ROIIC + (1−b)×OE/P + Δmultiple = 68.1%×17.6% + 31.9%×4.8% + (11.7/20.8)^(1/10)−1 = **8.0%** (holds year-one growth for all ten years, so it differs from the IRR).
- If the market keeps paying today's 20.8× owner earnings in year ten: 10.1%.
- Reverse DCF: to earn 10% from here, the market must pay **20.6× owner earnings in year ten** (base case: 11.7×). Holding the base terminal assumptions instead, no starting growth rate at the base-case ROIIC of 17.6% justifies today's price.

## Intrinsic value (Model §10 DCF)

Normalized owner earnings 1,321M = $1.35/share; net debt excl. leases -2,688M; 977.6M diluted shares.

| Case | r | Start g | Terminal g | ROIIC | IV/share | Terminal share | Exit multiple |
|---|---:|---:|---:|---:|---:|---:|---:|
| bear | 12% | 6.0% | 1.5% | 10.6% | $12.79 | 47% | 8.5× |
| base | 10% | 12.0% | 2.5% | 17.6% | $21.92 | 61% | 11.7× |
| bull | 10% | 12.1% | 3.0% | 17.6% | $24.82 | 70% | 12.2× |

Margin of safety vs base case: **-41%** (Model wants 20–30%).

**Price ladder** (base-case 10-year return): 8% → $25.15 · 10% → $21.92 · 12% → $19.24 · 15% → $16.03

## Ten-year record (USD millions)

| FY | Revenue | Net income | Owner earnings | OE/share | CFO−capex−SBC | ROIC | Diluted sh (M) |
|---|---|---|---|---|---|---|---|
| FY2016 | 1,268 | 270 | 218 | 0.22 | 138 | 27% | 977.2 |
| FY2017 | 1,448 | 394 | 383 | 0.40 | 299 | 26% | 948.1 |
| FY2018 | 1,806 | 418 | 399 | 0.41 | 224 | 29% | 967.5 |
| FY2019 | 2,042 | 592 | 443 | 0.46 | 249 | 31% | 961.8 |
| FY2020 | 2,206 | 700 | 315 | 0.33 | 303 | 29% | 954.6 |
| FY2021 | 2,693 | 936 | 894 | 0.93 | 487 | 34% | 961.2 |
| FY2022 | 3,501 | 1,090 | 1,020 | 1.06 | 800 | 36% | 964.6 |
| FY2023 | 3,870 | 1,238 | 1,127 | 1.17 | 808 | 29% | 966.6 |
| FY2024 | 4,237 | 1,363 | 1,291 | 1.32 | 926 | 23% | 974.8 |
| FY2025 | 4,647 | 1,552 | 1,321 | 1.35 | 1,193 | 22% | 977.6 |

Consistency tests: 10/10 positive OE years · OEPS CAGR 22.2% · 1 down years, worst -28.4% · longest recovery 2y · cash conversion 0.87×

## Balance sheet (latest year)

Debt 0M + operating leases 101M − excess cash 2,688M = net debt **-2,587M** (-1.96× OE; stressed -2.75×). Coverage 840× (stressed 840×). Not testable from XBRL facts: pension deficits, supplier financing, guarantees, litigation, maturity schedule.

## Data provenance

Source: SEC XBRL company facts, 10-K and 10-K/A filings only. 3 restated values detected (latest filing used). Normalization notes:

- revenue: tag changed over time -> RevenueFromContractWithCustomerIncludingAssessedTax | Revenues | SalesRevenueNet
- interest_expense: tag changed over time -> InterestExpense | InterestPaidNet
- cfo: tag changed over time -> NetCashProvidedByUsedInOperatingActivities | NetCashProvidedByUsedInOperatingActivitiesContinuingOperations
- buybacks: not reported for 2022-07, 2023-07, 2024-07, 2025-07; treated as 0
- acquisitions: missing for 2024-07 between reported years; left unknown
- WeightedAverageNumberOfDilutedSharesOutstanding 2012-07-31: value filed 2014-09-29 was off by 1000x (unscaled thousands); rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding 2013-07-31: value filed 2014-09-29 was off by 1000x (unscaled thousands); rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding 2014-07-31: value filed 2014-09-29 was off by 1000x (unscaled thousands); rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding: 2-for-1 stock split detected after filing of 2016-09-28; earlier values adjusted
- WeightedAverageNumberOfDilutedSharesOutstanding: 4-for-1 stock split detected after filing of 2022-09-27; earlier values adjusted
- equity: tag changed over time -> StockholdersEquity | StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest
- cash: tag changed over time -> CashAndCashEquivalentsAtCarryingValue | CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents
- long_term_debt: not reported for 2025-07; treated as 0
- long_term_debt: tag changed over time -> LongTermDebt | LongTermDebtAndCapitalLeaseObligations
- operating_leases: not reported for 2013-07, 2014-07, 2015-07, 2016-07, 2017-07, 2018-07; treated as 0
- operating_leases: tag changed over time -> OperatingLeaseLiability | OperatingLeaseLiabilityCurrent+OperatingLeaseLiabilityNoncurrent

*Analysis for one individual's own decision, not investment advice. A CANDIDATE is a prompt to study, never an instruction to buy.*
