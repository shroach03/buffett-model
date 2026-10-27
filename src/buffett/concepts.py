"""Mapping from the Model's inputs to XBRL tags.

Each concept lists *alternatives* in priority order. An alternative is a tuple
of tags that are summed. A tag ending in ``?`` is optional inside its
alternative (missing -> 0), but at least one tag in the alternative must be
present for it to match. Alternatives are resolved **per fiscal year**, so a
company that switched tags mid-decade (e.g. ``SalesRevenueNet`` ->
``RevenueFromContractWithCustomerExcludingAssessedTax`` after ASC 606 in 2018)
still yields one continuous series. The winning tag for every year is logged.

``if_missing`` says what happens when no alternative matches in a year:
  * ``"unknown"`` -> None. Downstream math propagates None rather than
    guessing. This is the Model's rule: silent gaps become a wider margin of
    safety, never a silent zero.
  * ``"zero"`` -> 0, with a note. Used only for items where absence normally
    means "none" (dividends at a company that pays none, short-term
    investments, acquisitions). Every zero-fill is recorded in the notes.

``flag`` marks alternatives that are a less exact substitute (e.g. net income
including noncontrolling interests); a flagged pick is reported.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Alt:
    tags: tuple[str, ...]
    flag: str | None = None


@dataclass(frozen=True)
class Concept:
    name: str
    kind: str  # "duration" (income / cash-flow) or "instant" (balance sheet)
    alts: tuple[Alt, ...]
    unit: str = "USD"
    if_missing: str = "unknown"
    description: str = ""


def A(*tags: str, flag: str | None = None) -> Alt:
    return Alt(tuple(tags), flag)


CONCEPTS: tuple[Concept, ...] = (
    # ---- income statement (durations) -------------------------------------
    Concept(
        "revenue",
        "duration",
        (
            A("Revenues"),
            A("RevenueFromContractWithCustomerExcludingAssessedTax"),
            A("RevenueFromContractWithCustomerIncludingAssessedTax"),
            A("SalesRevenueNet"),
            A("SalesRevenueGoodsNet?", "SalesRevenueServicesNet?", flag="sum of goods + services revenue"),
        ),
        description="Total revenue",
    ),
    Concept("gross_profit", "duration", (A("GrossProfit"),)),
    Concept("operating_income", "duration", (A("OperatingIncomeLoss"),), description="EBIT proxy"),
    Concept(
        "pretax_income",
        "duration",
        (
            A("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"),
            A(
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"
            ),
        ),
    ),
    Concept("income_tax", "duration", (A("IncomeTaxExpenseBenefit"),)),
    Concept(
        "net_income",
        "duration",
        (
            A("NetIncomeLoss"),
            A("NetIncomeLossAvailableToCommonStockholdersBasic"),
            A("ProfitLoss", flag="includes noncontrolling interests"),
        ),
        description="Net income attributable to common",
    ),
    Concept(
        "interest_expense",
        "duration",
        (
            A("InterestExpense"),
            A("InterestExpenseNonoperating"),
            A("InterestExpenseDebt"),
            A("InterestPaidNet", flag="cash interest paid, not expense"),
            A("InterestPaid", flag="cash interest paid, not expense"),
        ),
        if_missing="zero",
    ),
    # ---- cash flow (durations) -------------------------------------------
    Concept(
        "da",
        "duration",
        (
            A("DepreciationDepletionAndAmortization"),
            A("DepreciationAmortizationAndAccretionNet"),
            A("DepreciationAndAmortization"),
            A("Depreciation", "AmortizationOfIntangibleAssets?", flag="depreciation + intangible amortization (sum)"),
        ),
        description="Depreciation and amortization",
    ),
    Concept(
        "cfo",
        "duration",
        (
            A("NetCashProvidedByUsedInOperatingActivities"),
            A("NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"),
        ),
        description="Cash from operations",
    ),
    Concept(
        "capex",
        "duration",
        (
            A("PaymentsToAcquirePropertyPlantAndEquipment"),
            A("PaymentsToAcquireProductiveAssets"),
        ),
        description="Total capital expenditures",
    ),
    Concept(
        "sbc",
        "duration",
        (
            A("ShareBasedCompensation"),
            A("AllocatedShareBasedCompensationExpense"),
        ),
        if_missing="zero",
        description="Stock-based compensation",
    ),
    Concept(
        "dividends",
        "duration",
        (
            A("PaymentsOfDividendsCommonStock"),
            A("PaymentsOfDividends"),
        ),
        if_missing="zero",
    ),
    Concept("buybacks", "duration", (A("PaymentsForRepurchaseOfCommonStock"),), if_missing="zero"),
    Concept("acquisitions", "duration", (A("PaymentsToAcquireBusinessesNetOfCashAcquired"),), if_missing="zero"),
    Concept(
        "impairments",
        "duration",
        (
            A("GoodwillAndIntangibleAssetImpairment"),
            A("GoodwillImpairmentLoss?", "ImpairmentOfIntangibleAssetsExcludingGoodwill?"),
            A("AssetImpairmentCharges"),
            A("ImpairmentOfLongLivedAssetsHeldForUse"),
        ),
        if_missing="zero",
        description="Non-cash impairment charges (added back in owner earnings)",
    ),
    Concept("diluted_shares", "duration", (A("WeightedAverageNumberOfDilutedSharesOutstanding"),), unit="shares"),
    # ---- balance sheet (instants) ------------------------------------------
    Concept("total_assets", "instant", (A("Assets"),)),
    Concept("current_assets", "instant", (A("AssetsCurrent"),)),
    Concept("current_liabilities", "instant", (A("LiabilitiesCurrent"),)),
    Concept(
        "equity",
        "instant",
        (
            A("StockholdersEquity"),
            A(
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
                flag="includes noncontrolling interests",
            ),
        ),
    ),
    Concept(
        "cash",
        "instant",
        (
            A("CashAndCashEquivalentsAtCarryingValue"),
            A("CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", flag="includes restricted cash"),
        ),
    ),
    Concept(
        "st_investments",
        "instant",
        (
            A("ShortTermInvestments"),
            A("MarketableSecuritiesCurrent"),
            A("AvailableForSaleSecuritiesDebtSecuritiesCurrent"),
        ),
        if_missing="zero",
    ),
    Concept(
        "long_term_debt",
        "instant",
        (
            A("LongTermDebt"),
            A("LongTermDebtAndCapitalLeaseObligations?", "LongTermDebtAndCapitalLeaseObligationsCurrent?"),
            A("LongTermDebtNoncurrent?", "LongTermDebtCurrent?", "DebtCurrent?"),
            A("LongTermLineOfCredit?", "LinesOfCreditCurrent?"),
        ),
        if_missing="zero",
        description="Long-term debt incl. current portion",
    ),
    Concept("short_term_debt", "instant", (A("ShortTermBorrowings?", "CommercialPaper?"),), if_missing="zero"),
    Concept(
        "operating_leases",
        "instant",
        (
            A("OperatingLeaseLiability"),
            A("OperatingLeaseLiabilityCurrent?", "OperatingLeaseLiabilityNoncurrent?"),
        ),
        if_missing="zero",
        description="Operating lease liabilities (on balance sheet from 2019, ASC 842)",
    ),
    Concept("ppe_net", "instant", (A("PropertyPlantAndEquipmentNet"),)),
    Concept("goodwill", "instant", (A("Goodwill"),), if_missing="zero"),
)

BY_NAME = {c.name: c for c in CONCEPTS}
