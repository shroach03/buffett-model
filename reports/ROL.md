# ROL · Rollins, Inc.

**Verdict: WAIT**, quality passes; expected return 3.3% < 10% hurdle; margin of safety -72.4% < 20%; total 64/100 < 75  
Latest annual data: FY2025 10-K (period ending 2025-12-31) · Price: $33.53 (2026-09-16)

## Scorecard

| Category | Points | Max | Basis |
|---|---:|---:|---|
| Understandability & moat | 14 | 15 | judgment: Opportunity brief of 2026-08-03 (LLM-assisted chat session, reviewed by the user; not independently verified). Replace with your own read. |
| Earnings quality & consistency | 15 | 15 | 10/10 positive OE yrs; OEPS CAGR 14.6%; worst drawdown -5.2%; conversion 1.18x |
| Returns on capital | 20 | 20 | median ROE 32.5%; median ROIC 29.5%; 5y ROIIC 30.7%; worst ROIC 26.7% |
| Balance-sheet strength | 8 | 10 | net debt incl. leases 1,013M = 1.63x OE; coverage 25x |
| Management & allocation | 7 | 10 | judgment (see notes); share count -0.2%/yr over 10y |
| **Quality subtotal** (≥ 55) | **64** | 70 | |
| Valuation & expected return | 0 | 20 | conservative 10y IRR 3.3% |
| Margin of safety | 0 | 10 | discount to base-case IV -72.4% |
| **Total** (≥ 75) | **64** | 100 | |

**Fatal flaws:** none detected in the data

**Judgment notes (2026-08-03):** Moat: route density, ~75% recurring revenue. Management: 2022 SEC settlement under prior management (resolved); CFO departed Jun 2026; family control. Growth leans on acquisitions.

## Expected return

- **Base-case 10-year IRR: 3.3%** vs 10% hurdle. Growth starts at g = b × ROIIC = 39.2% × 29.5% = 11.6% and fades to 2.5%; exit at the base case's own value, 12.5× OE.
- Model shorthand: R ≈ b×ROIIC + (1−b)×OE/P + Δmultiple = 39.2%×29.5% + 60.8%×3.7% + (12.5/27.0)^(1/10)−1 = **6.4%** (holds year-one growth for all ten years, so it differs from the IRR).
- If the market keeps paying today's 27.0× owner earnings in year ten: 9.8%.
- Reverse DCF: to earn 10% from here, the market must pay **27.6× owner earnings in year ten** (base case: 12.5×). Holding the base terminal assumptions instead, no starting growth rate at the base-case ROIIC of 29.5% justifies today's price.

## Intrinsic value (Model §10 DCF)

Normalized owner earnings 623M = $1.29/share; net debt excl. leases 585M; 484.1M diluted shares.

| Case | r | Start g | Terminal g | ROIIC | IV/share | Terminal share | Exit multiple |
|---|---:|---:|---:|---:|---:|---:|---:|
| bear | 12% | 5.8% | 1.5% | 17.7% | $9.49 | 41% | 8.5× |
| base | 10% | 11.6% | 2.5% | 29.5% | $19.45 | 57% | 12.5× |
| bull | 10% | 12.0% | 3.0% | 30.7% | $24.12 | 63% | 13.3× |

Margin of safety vs base case: **-72%** (Model wants 20–30%).

**Price ladder** (base-case 10-year return): 8% → $22.77 · 10% → $19.45 · 12% → $16.68 · 15% → $13.35

## Ten-year record (USD millions)

| FY | Revenue | Net income | Owner earnings | OE/share | CFO−capex−SBC | ROIC | Diluted sh (M) |
|---|---|---|---|---|---|---|---|
| FY2016 | 1,573 | 167 | 185 | 0.38 | 181 | 44% | 491.0 |
| FY2017 | 1,674 | 179 | 211 | 0.43 | 198 | 42% | 490.5 |
| FY2018 | 1,822 | 232 | 271 | 0.55 | 258 | 38% | 490.9 |
| FY2019 | 2,015 | 203 | 257 | 0.52 | 278 | 29% | 491.2 |
| FY2020 | 2,161 | 267 | 332 | 0.68 | 392 | 27% | 491.6 |
| FY2021 | 2,424 | 357 | 416 | 0.85 | 360 | 29% | 492.1 |
| FY2022 | 2,696 | 369 | 429 | 0.87 | 414 | 29% | 492.4 |
| FY2023 | 3,073 | 435 | 502 | 1.02 | 471 | 30% | 490.1 |
| FY2024 | 3,389 | 466 | 552 | 1.14 | 550 | 30% | 484.3 |
| FY2025 | 3,761 | 527 | 623 | 1.29 | 610 | 29% | 484.1 |

Consistency tests: 10/10 positive OE years · OEPS CAGR 14.6% · 1 down years, worst -5.2% · longest recovery 2y · cash conversion 1.18×

## Balance sheet (latest year)

Debt 610M + operating leases 428M − excess cash 25M = net debt **1,013M** (1.63× OE; stressed 1.71×). Coverage 25× (stressed 25×). Not testable from XBRL facts: pension deficits, supplier financing, guarantees, litigation, maturity schedule.

## Data provenance

Source: SEC XBRL company facts, 10-K and 10-K/A filings only. 22 restated values detected (latest filing used). Normalization notes:

- revenue: tag changed over time -> RevenueFromContractWithCustomerExcludingAssessedTax | Revenues | SalesRevenueServicesNet
- pretax_income: tag changed over time -> IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments
- net_income: tag changed over time -> NetIncomeLoss | NetIncomeLossAvailableToCommonStockholdersBasic
- interest_expense: not reported for 2013-12, 2014-12; treated as 0
- interest_expense: tag changed over time -> InterestExpenseNonoperating | InterestPaidNet
- da: tag changed over time -> DepreciationAndAmortization | DepreciationDepletionAndAmortization
- cfo: tag changed over time -> NetCashProvidedByUsedInOperatingActivities | NetCashProvidedByUsedInOperatingActivitiesContinuingOperations
- impairments: not reported for 2013-12, 2014-12, 2015-12, 2016-12, 2017-12, 2018-12, 2019-12, 2020-12; treated as 0
- WeightedAverageNumberOfDilutedSharesOutstanding 2012-12-31: value filed 2015-02-25 was off by 1000x (unscaled thousands); rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding 2013-12-31: value filed 2015-02-25 was off by 1000x (unscaled thousands); rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding 2014-12-31: value filed 2015-02-25 was off by 1000x (unscaled thousands); rescaled
- WeightedAverageNumberOfDilutedSharesOutstanding: 1.5-for-1 stock split detected after filing of 2015-02-25; earlier values adjusted
- WeightedAverageNumberOfDilutedSharesOutstanding: 1.5-for-1 stock split detected after filing of 2018-02-26; earlier values adjusted
- WeightedAverageNumberOfDilutedSharesOutstanding: 1.5-for-1 stock split detected after filing of 2020-02-28; earlier values adjusted
- long_term_debt: not reported for 2013-12, 2014-12, 2015-12, 2016-12, 2017-12, 2018-12; treated as 0
- long_term_debt: tag changed over time -> LongTermDebt | LongTermLineOfCredit+LinesOfCreditCurrent
- short_term_debt: not reported for 2013-12, 2014-12, 2015-12, 2016-12, 2017-12, 2018-12, 2019-12, 2020-12, 2021-12, 2022-12, 2023-12; treated as 0
- operating_leases: not reported for 2013-12, 2014-12, 2015-12, 2016-12, 2017-12, 2018-12, 2019-12; treated as 0
- operating_leases: tag changed over time -> OperatingLeaseLiability | OperatingLeaseLiabilityCurrent+OperatingLeaseLiabilityNoncurrent

*Analysis for one individual's own decision, not investment advice. A CANDIDATE is a prompt to study, never an instruction to buy.*
