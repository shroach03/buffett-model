"""Turn raw SEC companyfacts JSON into one clean row per fiscal year.

The hard parts, each handled explicitly here:

* Duplicates: every 10-K repeats the prior two years for comparison, so each
  period appears in up to three filings. Facts are keyed on the period's
  actual start/end dates, never on the filing's ``fy`` label, which describes
  the filing rather than the period.
* Restatements: when those repeated values disagree, the most recently filed
  value wins and the change is logged (frequent restatements are themselves an
  accounting-quality signal under the Model).
* Durations vs. snapshots: income and cash-flow items must span ~12 months;
  10-Ks also contain quarterly and year-to-date durations, which are dropped.
  Balance-sheet items are instants matched to the fiscal year-end date.
* Fiscal calendars: Copart's year ends July 31 and Graco's 52/53-week year
  ends on the last Friday of December, so periods are matched to the
  company's own year-end dates with a few days' tolerance.
* Tag drift and missing tags: see ``concepts.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .concepts import CONCEPTS, Concept

ANNUAL_DAYS = (350, 380)
END_TOLERANCE_DAYS = 6
RESTATEMENT_THRESHOLD = 0.005  # log restatements that move a value by >0.5%


@dataclass
class Restatement:
    tag: str
    period_end: str
    old: float
    new: float
    old_filed: str
    new_filed: str

    @property
    def pct(self) -> float:
        return (self.new - self.old) / abs(self.old) if self.old else float("inf")


@dataclass
class Financials:
    ticker: str
    name: str
    years: list[str]                      # fiscal year-end dates, ascending (ISO)
    data: dict[str, list[float | None]]   # concept -> values aligned with years
    source: dict[str, list[str | None]]   # concept -> winning tag(s) per year
    restatements: list[Restatement] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def __getitem__(self, concept: str) -> list[float | None]:
        return self.data[concept]

    def fy_labels(self) -> list[str]:
        return [f"FY{y[:4]}" if y[5:7] >= "06" else f"FY{int(y[:4]) - 1}" for y in self.years]

    def coverage(self) -> dict[str, float]:
        return {k: sum(v is not None for v in vals) / len(vals) for k, vals in self.data.items()}

    def to_frame(self):
        import pandas as pd

        return pd.DataFrame(self.data, index=pd.Index(self.fy_labels(), name="fiscal_year"))


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _close(a: str, b: str) -> bool:
    return abs((_d(a) - _d(b)).days) <= END_TOLERANCE_DAYS


def _is_annual(fact: dict) -> bool:
    if not fact.get("start"):
        return False
    days = (_d(fact["end"]) - _d(fact["start"])).days
    return ANNUAL_DAYS[0] <= days <= ANNUAL_DAYS[1]


def _series(facts: dict, tag: str, unit: str, kind: str, log: list[Restatement]) -> dict[str, dict]:
    """All values for one tag, one per period end (latest filing wins)."""
    node = facts.get("facts", {}).get("us-gaap", {}).get(tag)
    if not node or unit not in node["units"]:
        return {}
    by_end: dict[str, list[dict]] = {}
    for f in node["units"][unit]:
        if not f.get("form", "").startswith("10-K"):
            continue
        if kind == "duration" and not _is_annual(f):
            continue
        if kind == "instant" and f.get("start"):
            continue
        by_end.setdefault(f["end"], []).append(f)
    out = {}
    for end, group in by_end.items():
        group.sort(key=lambda f: f["filed"])
        latest = group[-1]
        for older in group[:-1]:
            if older["val"] != latest["val"]:
                base = abs(older["val"]) or 1
                if abs(latest["val"] - older["val"]) / base > RESTATEMENT_THRESHOLD:
                    log.append(Restatement(tag, end, older["val"], latest["val"], older["filed"], latest["filed"]))
        out[end] = latest
    return out


SPLIT_FACTORS = (1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0)


def _split_like(ratio: float) -> float | None:
    for f in SPLIT_FACTORS:
        if abs(ratio / f - 1) < 0.03:
            return f
    return None


def _adjust_share_series(facts: dict, tag: str, kind: str) -> tuple[dict[str, dict], list[str]]:
    """Share counts on today's basis, correcting two problems in the raw data.

    1. Scale errors: some older filings tagged share counts in thousands
       without the scale factor (e.g. Copart FY2013 reported as 129,781 rather
       than 129,781,000). A value ~1000x smaller than the same period's value
       in another filing is rescaled.
    2. Stock splits: a 10-K restates only the prior two years on the new
       basis, so years older than that stay on the pre-split basis and a raw
       series shows a fake jump. A split is detected when the same period is
       reported with a split-like ratio (3:2, 2:1, ...) in two filings; it
       happened after the last filing that used the old basis. Every value
       whose latest filing predates the split is multiplied by the factor.
    """
    node = facts.get("facts", {}).get("us-gaap", {}).get(tag)
    if not node or "shares" not in node["units"]:
        return {}, []
    notes: list[str] = []
    by_end: dict[str, list[dict]] = {}
    for f in node["units"]["shares"]:
        if not f.get("form", "").startswith("10-K"):
            continue
        if kind == "duration" and not _is_annual(f):
            continue
        by_end.setdefault(f["end"], []).append(dict(f))
    # 1. scale errors
    for end, group in by_end.items():
        big = max(g["val"] for g in group)
        for g in group:
            if g["val"] and 500 < big / g["val"] < 2000 * 10:
                g["val"] *= 1000
                notes.append(f"{tag} {end}: value filed {g['filed']} was off by 1000x (unscaled thousands); rescaled")
    # A lone value with no second filing can still be unscaled; compare with neighbours.
    ends = sorted(by_end)
    for i, end in enumerate(ends):
        group = by_end[end]
        latest = max(group, key=lambda g: g["filed"])
        neighbours = [max(by_end[e], key=lambda g: g["filed"])["val"] for e in ends[max(0, i - 2):i + 3] if e != end]
        if neighbours and latest["val"] and min(neighbours) / latest["val"] > 500:
            latest["val"] *= 1000
            notes.append(f"{tag} {end}: value off by 1000x vs neighbouring years; rescaled")
    # 2. splits
    events: list[tuple[str, float]] = []  # (split happened after this filing date, factor)
    for end, group in by_end.items():
        group.sort(key=lambda g: g["filed"])
        for old, new in zip(group, group[1:]):
            if old["val"] and new["val"] != old["val"]:
                f = _split_like(new["val"] / old["val"])
                if f:
                    events.append((old["filed"], f))
    merged: list[tuple[str, float]] = []
    for after, f in sorted(events):
        if merged and merged[-1][1] == f and (_d(after) - _d(merged[-1][0])).days < 330:
            merged[-1] = (max(after, merged[-1][0]), f)
        else:
            merged.append((after, f))
    for after, f in merged:
        notes.append(f"{tag}: {f:g}-for-1 stock split detected after filing of {after}; earlier values adjusted")
    out = {}
    for end, group in by_end.items():
        latest = dict(max(group, key=lambda g: g["filed"]))
        for after, f in merged:
            if latest["filed"] <= after:
                latest["val"] *= f
        out[end] = latest
    return out, notes


def fiscal_year_ends(facts: dict, n_years: int) -> list[str]:
    """The company's own fiscal year-end dates, from its annual net-income facts."""
    ends: list[str] = []
    for tag in ("NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic", "ProfitLoss"):
        for e in sorted(_series(facts, tag, "USD", "duration", [])):
            if not any(_close(e, x) for x in ends):
                ends.append(e)
    ends.sort()
    return ends[-n_years:]


def _resolve(concept: Concept, year_end: str, cache: dict) -> tuple[float | None, str | None, str | None]:
    for alt in concept.alts:
        total, used, any_present = 0.0, [], False
        ok = True
        for raw in alt.tags:
            optional = raw.endswith("?")
            tag = raw.rstrip("?")
            series = cache[tag]
            hit = next((f for e, f in series.items() if _close(e, year_end)), None)
            if hit is None:
                if not optional:
                    ok = False
                    break
                continue
            any_present = True
            total += hit["val"]
            used.append(tag)
        if ok and any_present:
            return total, "+".join(used), alt.flag
    return None, None, None


def build_financials(facts: dict, ticker: str, n_years: int = 13) -> Financials:
    restatements: list[Restatement] = []
    years = fiscal_year_ends(facts, n_years)
    data, source, notes, flags = {}, {}, [], []

    for c in CONCEPTS:
        cache = {}
        for alt in c.alts:
            for raw in alt.tags:
                tag = raw.rstrip("?")
                if tag in cache:
                    continue
                if c.unit == "shares":
                    cache[tag], share_notes = _adjust_share_series(facts, tag, c.kind)
                    notes.extend(share_notes)
                else:
                    cache[tag] = _series(facts, tag, c.unit, c.kind, restatements)
        vals, srcs = [], []
        for y in years:
            v, s, flag = _resolve(c, y, cache)
            if flag:
                flags.append(f"{c.name} {y[:7]}: {s} ({flag})")
            vals.append(v)
            srcs.append(s)
        # Zero-fill policy: before the first or after the last year a tag was
        # reported, absence means "none" (e.g. no leases on balance sheet before
        # ASC 842, debt fully repaid). A gap *between* reported years is unknown.
        if c.if_missing == "zero":
            present = [i for i, v in enumerate(vals) if v is not None]
            zero_filled, gaps = [], []
            for i, v in enumerate(vals):
                if v is not None:
                    continue
                if not present or i < present[0] or i > present[-1]:
                    vals[i], srcs[i] = 0.0, "absent->0"
                    zero_filled.append(years[i][:7])
                else:
                    gaps.append(years[i][:7])
            if zero_filled and present:
                notes.append(f"{c.name}: not reported for {', '.join(zero_filled)}; treated as 0")
            if gaps:
                notes.append(f"{c.name}: missing for {', '.join(gaps)} between reported years; left unknown")
        data[c.name], source[c.name] = vals, srcs
        tags_used = sorted({s for s in srcs if s and s != "absent->0"})
        if len(tags_used) > 1:
            notes.append(f"{c.name}: tag changed over time -> {' | '.join(tags_used)}")

    # Derived fallback: EBIT = pretax income + interest when OperatingIncomeLoss is absent.
    for i, v in enumerate(data["operating_income"]):
        if v is None and data["pretax_income"][i] is not None:
            data["operating_income"][i] = data["pretax_income"][i] + (data["interest_expense"][i] or 0.0)
            source["operating_income"][i] = "derived: pretax_income + interest_expense"
            flags.append(f"operating_income {years[i][:7]}: derived from pretax + interest")

    # Keep only restatements of tags we actually used, deduplicated.
    used_tags = {t for srcs in source.values() for s in srcs if s for t in s.split("+")}
    seen, kept = set(), []
    for r in restatements:
        key = (r.tag, r.period_end, r.old, r.new)
        if r.tag in used_tags and key not in seen and any(_close(r.period_end, y) for y in years):
            seen.add(key)
            kept.append(r)

    return Financials(
        ticker=ticker.upper(),
        name=facts.get("entityName", ticker),
        years=years,
        data=data,
        source=source,
        restatements=kept,
        notes=notes,
        flags=flags,
    )
