# WAT · Waters Corporation

**Verdict: PASS**, fatal flaw: leverage: the BD Biosciences & Diagnostics merger (closed Feb 2026) added ~$4B of debt and nearly doubled the share count; the FY2025 10-K data used here predates it  
Latest annual data: FY2025 10-K (period ending 2025-12-31) · Price: $418.64 (2026-09-16)

> ⚠ only 3 of 10 years of owner earnings computable (missing inputs are left unknown, not estimated)

## Scorecard

| Category | Points | Max | Basis |
|---|---:|---:|---|
| Understandability & moat | 10 | 15 | judgment: Opportunity brief of 2026-08-03 (LLM-assisted chat session, reviewed by the user; not independently verified). Replace with your own read. |
| Earnings quality & consistency | 8 | 15 | 3/3 positive OE yrs; OEPS CAGR 3.7%; worst drawdown n/a; conversion 1.06x |
| Returns on capital | 15 | 20 | median ROE 60.2%; median ROIC 47.8%; 5y ROIIC 6.0%; worst ROIC 20.7% |
| Balance-sheet strength | 7 | 10 | net debt incl. leases 969M = 1.38x OE; coverage 12x |
| Management & allocation | 6 | 10 | judgment (see notes); share count -3.4%/yr over 10y |
| **Quality subtotal** (≥ 55) | **46** | 70 | |
| Valuation & expected return | 0 | 20 | conservative 10y IRR -8.6% |
| Margin of safety | 0 | 10 | discount to base-case IV -467.8% |
| **Total** (≥ 75) | **46** | 100 | |

**Fatal flaws:** leverage: the BD Biosciences & Diagnostics merger (closed Feb 2026) added ~$4B of debt and nearly doubled the share count; the FY2025 10-K data used here predates it

**Judgment notes (2026-08-03):** Legacy moat strong (razor/blade instruments + consumables); combined entity unproven. The code's numbers describe pre-merger Waters.

## Expected return

- **Base-case 10-year IRR: -8.6%** vs 10% hurdle. Growth starts at g = b × ROIIC = 63.6% × 6.0% = 3.8% and fades to 2.5%; exit at the base case's own value, 7.9× OE.
- Model shorthand: R ≈ b×ROIIC + (1−b)×OE/P + Δmultiple = 63.6%×6.0% + 36.4%×2.7% + (7.9/36.9)^(1/10)−1 = **-9.5%** (holds year-one growth for all ten years, so it differs from the IRR).
- If the market keeps paying today's 36.9× owner earnings in year ten: 4.4%.
- Reverse DCF: to earn 10% from here, the market must pay **64.2× owner earnings in year ten** (base case: 7.9×). Holding the base terminal assumptions instead, no starting growth rate at the base-case ROIIC of 6.0% justifies today's price.

## Intrinsic value (Model §10 DCF)

Normalized owner earnings 701M = $11.75/share; net debt excl. leases 885M; 59.7M diluted shares.

| Case | r | Start g | Terminal g | ROIIC | IV/share | Terminal share | Exit multiple |
|---|---:|---:|---:|---:|---:|---:|---:|
| bear | 12% | 1.9% | 1.5% | 3.6% | $53.00 | 50% | 8.5× |
| base | 10% | 3.8% | 2.5% | 6.0% | $73.73 | 55% | 7.9× |
| bull | 10% | 3.8% | 3.0% | 6.0% | $66.31 | 58% | 7.3× |

Margin of safety vs base case: **-468%** (Model wants 20–30%).

**Price ladder** (base-case 10-year return): 8% → $87.70 · 10% → $73.73 · 12% → $62.10 · 15% → $48.09

## Ten-year record (USD millions)

| FY | Revenue | Net income | Owner earnings | OE/share | CFO−capex−SBC | ROIC | Diluted sh (M) |
|---|---|---|---|---|---|---|---|
| FY2016 | 2,167 | 522 | n/a | n/a | n/a | 39% | 81.4 |
| FY2017 | 2,309 | 20 | n/a | n/a | n/a | 50% | 80.6 |
| FY2018 | 2,420 | 594 | n/a | n/a | n/a | 66% | 77.6 |
| FY2019 | 2,407 | 592 | n/a | n/a | n/a | 55% | 68.2 |
| FY2020 | 2,365 | 522 | n/a | n/a | n/a | 46% | 62.4 |
| FY2021 | 2,786 | 693 | n/a | n/a | n/a | 55% | 62.0 |
| FY2022 | 2,972 | 708 | n/a | n/a | n/a | 49% | 60.3 |
| FY2023 | 2,956 | 642 | 647 | 10.92 | 405 | 29% | 59.3 |
| FY2024 | 2,958 | 638 | 687 | 11.54 | 575 | 22% | 59.6 |
| FY2025 | 3,165 | 643 | 701 | 11.75 | 486 | 21% | 59.7 |

Consistency tests: 3/3 positive OE years · OEPS CAGR 3.7% · 0 down years, worst n/a · longest recovery 0y · cash conversion 1.06×

## Balance sheet (latest year)

Debt 1,410M + operating leases 84M − excess cash 525M = net debt **969M** (1.38× OE; stressed 1.38×). Coverage 12× (stressed 11×). Not testable from XBRL facts: pension deficits, supplier financing, guarantees, litigation, maturity schedule.

## Data provenance

Source: SEC XBRL company facts, 10-K and 10-K/A filings only. 3 restated values detected (latest filing used). Normalization notes:

- revenue: tag changed over time -> RevenueFromContractWithCustomerExcludingAssessedTax | SalesRevenueNet
- net_income: tag changed over time -> NetIncomeLoss | NetIncomeLossAvailableToCommonStockholdersBasic
- da: tag changed over time -> Depreciation | Depreciation+AmortizationOfIntangibleAssets
- cfo: tag changed over time -> NetCashProvidedByUsedInOperatingActivities | NetCashProvidedByUsedInOperatingActivitiesContinuingOperations
- acquisitions: missing for 2017-12 between reported years; left unknown
- impairments: not reported for 2013-12, 2014-12, 2015-12, 2016-12, 2017-12, 2018-12, 2023-12, 2024-12, 2025-12; treated as 0
- st_investments: not reported for 2025-12; treated as 0
- long_term_debt: tag changed over time -> LongTermDebt | LongTermDebtNoncurrent+DebtCurrent
- operating_leases: not reported for 2013-12, 2014-12, 2015-12, 2016-12, 2017-12; treated as 0

*Analysis for one individual's own decision, not investment advice. A CANDIDATE is a prompt to study, never an instruction to buy.*
