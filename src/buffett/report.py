"""Render an analysis Result as a Markdown opportunity brief."""

from __future__ import annotations

from .analysis import Result
from .balance_sheet import BalanceSheet


def _m(x):
    return "n/a" if x is None else f"{x / 1e6:,.0f}"


def _p(x, d=1):
    return "n/a" if x is None else f"{x:.{d}%}"


def _x(x, d=1):
    return "n/a" if x is None else f"{x:.{d}f}×"


def _usd(x):
    return "n/a" if x is None else f"${x:,.2f}"


def brief(r: Result) -> str:
    sections = (_header, _scorecard, _expected_return, _intrinsic_value, _ten_year, _balance_sheet, _provenance)
    return "\n".join(line for section in sections for line in section(r))


def _header(r: Result) -> list[str]:
    """Title, verdict, data date and warnings."""
    f, d = r.fin, r.decision
    fy = f.fy_labels()
    out = []
    price_line = f"{_usd(r.price)} ({r.price_date})" if r.price else "no price supplied"
    out.append(f"# {r.ticker} · {f.name.title()}\n")
    out.append(f"**Verdict: {d.verdict}**, {d.reason}  ")
    out.append(f"Latest annual data: {fy[-1]} 10-K (period ending {f.years[-1]}) · Price: {price_line}\n")
    if r.warnings:
        out.append("> " + "  \n> ".join("⚠ " + w for w in r.warnings) + "\n")
    return out


def _scorecard(r: Result) -> list[str]:
    """Model §2: the 100-point table, fatal flaws and judgment notes."""
    d = r.decision
    out = []
    out.append("## Scorecard\n")
    out.append("| Category | Points | Max | Basis |\n|---|---:|---:|---|")
    j = r.judgment
    out.append(
        f"| Understandability & moat | {j.moat if j else '—'} | 15 | "
        f"{'judgment: ' + j.source if j else 'needs a judgment input'} |"
    )
    for line in r.lines[:3]:
        out.append(f"| {line.category} | {line.points} | {line.max_points} | {line.basis} |")
    out.append(
        f"| Management & allocation | {j.management if j else '—'} | 10 | "
        f"{'judgment (see notes)' if j else 'needs a judgment input'}; share count "
        f"{_p(_share_cagr(r))}/yr over 10y |"
    )
    q = d.quality if d.quality is not None else f"{d.quant_quality} + judgment"
    out.append(f"| **Quality subtotal** (≥ 55) | **{q}** | 70 | |")
    for line in r.lines[3:]:
        out.append(f"| {line.category} | {line.points} | {line.max_points} | {line.basis} |")
    t = d.total if d.total is not None else "—"
    out.append(f"| **Total** (≥ 75) | **{t}** | 100 | |\n")
    fatal = d.fatal or ["none detected in the data"]
    out.append("**Fatal flaws:** " + "; ".join(fatal) + "\n")
    if j and j.notes:
        out.append(f"**Judgment notes ({j.date}):** {j.notes}\n")
    return out


def _expected_return(r: Result) -> list[str]:
    """Model §1, §11: base-case IRR, the shorthand equation and the reverse DCF."""
    i = r.inputs
    out = []
    out.append("## Expected return\n")
    if r.expected_return_irr is not None:
        out.append(
            f"- **Base-case 10-year IRR: {_p(r.expected_return_irr)}** vs {_p(i['hurdle'], 0)} hurdle. "
            f"Growth starts at g = b × ROIIC = {_p(i['b_base'])} × {_p(i['roiic_base'])} = {_p(i['g_base'])} "
            f"and fades to 2.5%; exit at the base case's own value, {i['base_exit_multiple']:.1f}× OE."
        )
        out.append(
            f"- Model shorthand: R ≈ b×ROIIC + (1−b)×OE/P + Δmultiple = {_p(i['b_base'])}×{_p(i['roiic_base'])} "
            f"+ {_p(1 - i['b_base'])}×{_p(1 / i['p_oe'])} + ({i['base_exit_multiple']:.1f}/{i['p_oe']:.1f})^(1/10)−1 "
            f"= **{_p(r.expected_return_eq)}** (holds year-one growth for all ten years, so it differs from the IRR)."
        )
        out.append(
            f"- If the market keeps paying today's {i['p_oe']:.1f}× owner earnings in year ten: "
            f"{_p(r.expected_return_no_rerating)}."
        )
        rev = (
            f"justifying today's price takes {_p(r.reverse_dcf_g)} starting growth"
            if r.reverse_dcf_g is not None
            else f"no starting growth rate at the base-case ROIIC of {_p(i['roiic_base'])} justifies today's price"
        )
        out.append(
            f"- Reverse DCF: to earn {_p(i['hurdle'], 0)} from here, the market must pay "
            f"**{i['required_exit_multiple']:.1f}× "
            f"owner earnings in year ten** (base case: {i['base_exit_multiple']:.1f}×). "
            f"Holding the base terminal assumptions instead, {rev}.\n"
        )
    else:
        why = (
            "no price"
            if not r.price
            else "the IRR could not be solved at this price"
            if r.cases
            else "missing owner earnings, returns or debt"
        )
        out.append("Not computable: " + why + "\n")
    return out


def _intrinsic_value(r: Result) -> list[str]:
    """Model §10, §12: bear/base/bull DCF table, margin of safety and price ladder."""
    i = r.inputs
    out = []
    if r.cases:
        out.append("## Intrinsic value (Model §10 DCF)\n")
        out.append(
            f"Normalized owner earnings {_m(r.normalized_oe)}M = {_usd(r.oeps)}/share; "
            f"net debt excl. leases {_m(i['net_debt_dcf'])}M; {i['shares'] / 1e6:,.1f}M diluted shares.\n"
        )
        out.append("| Case | r | Start g | Terminal g | ROIIC | IV/share | Terminal share | Exit multiple |")
        out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for c in r.cases:
            a = c.assumptions
            out.append(
                f"| {c.case} | {_p(a.discount_rate, 0)} | {_p(a.g_start)} | {_p(a.g_terminal)} | "
                f"{_p(a.roiic)} | {_usd(c.ivps)} | {_p(c.terminal_share, 0)} | "
                f"{c.implied_exit_multiple:.1f}× |"
            )
        if r.mos is not None:
            out.append(f"\nMargin of safety vs base case: **{_p(r.mos, 0)}** (Model wants 20–30%).\n")

    if r.ladder:
        out.append(
            "**Price ladder** (base-case 10-year return): "
            + " · ".join(f"{int(k * 100)}% → {_usd(v)}" for k, v in r.ladder.items())
            + "\n"
        )
    return out


def _ten_year(r: Result) -> list[str]:
    """The ten-year record and the Model §4 consistency tests."""
    f = r.fin
    fy = f.fy_labels()
    out = []
    out.append("## Ten-year record (USD millions)\n")
    cols = ["FY", "Revenue", "Net income", "Owner earnings", "OE/share", "CFO−capex−SBC", "ROIC", "Diluted sh (M)"]
    out.append("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols))
    for k in range(max(0, len(fy) - 10), len(fy)):
        oeps = r.oe.oe_per_share[k]
        sh = f["diluted_shares"][k]
        out.append(
            f"| {fy[k]} | {_m(f['revenue'][k])} | {_m(f['net_income'][k])} | {_m(r.oe.owner_earnings[k])} | "
            f"{'n/a' if oeps is None else f'{oeps:.2f}'} | {_m(r.oe.conservative_fcf[k])} | {_p(r.ret.roic[k], 0)} | "
            f"{'n/a' if sh is None else f'{sh / 1e6:,.1f}'} |"
        )
    cons = r.cons
    out.append(
        f"\nConsistency tests: {cons.positive_years}/{cons.years_available} positive OE years · "
        f"OEPS CAGR {_p(cons.oeps_cagr)} · {cons.down_years} down years, "
        f"worst {_p(cons.worst_one_year_decline)} · longest recovery {cons.longest_recovery_years}y · "
        f"cash conversion {_x(cons.cash_conversion, 2)}\n"
    )
    return out


def _balance_sheet(r: Result) -> list[str]:
    """Model §9: leverage and coverage, with what XBRL can't show."""
    out = []
    b = r.bs
    out.append("## Balance sheet (latest year)\n")
    out.append(
        f"Debt {_m(b.total_debt)}M + operating leases {_m(b.operating_leases)}M − excess cash "
        f"{_m(b.excess_cash)}M = net debt **{_m(b.net_debt)}M** "
        f"({'n/a' if b.net_debt_to_oe is None else f'{b.net_debt_to_oe:.2f}×'} OE; stressed "
        f"{'n/a' if b.stressed_net_debt_to_oe is None else f'{b.stressed_net_debt_to_oe:.2f}×'}). Coverage "
        f"{_coverage(b)} "
        f"(stressed {'n/a' if b.stressed_coverage is None else f'{b.stressed_coverage:,.0f}×'}). "
        "Not testable from XBRL facts: pension deficits, supplier financing, guarantees, litigation, "
        "maturity schedule.\n"
    )
    return out


def _coverage(b: BalanceSheet) -> str:
    if b.coverage_status == "no_interest":
        return "no interest expense"
    if b.coverage is None:
        return "unknown (debt or interest data missing)"
    return f"{b.coverage:,.0f}×"


def _provenance(r: Result) -> list[str]:
    """Data source, restatements, normalization notes and the disclaimer."""
    f = r.fin
    out = []
    out.append("## Data provenance\n")
    out.append(
        "Source: SEC XBRL company facts, 10-K and 10-K/A filings only. "
        f"{len(f.restatements)} restated values detected (latest filing used). Normalization notes:\n"
    )
    for n in f.notes:
        out.append(f"- {n}")
    if r.ret.roiic_note:
        out.append(f"- ROIIC: {r.ret.roiic_note}")
    out.append(
        "\n*Analysis for one individual's own decision, not investment advice. "
        "A CANDIDATE is a prompt to study, never an instruction to buy.*\n"
    )
    return out


def _share_cagr(r: Result):
    sh = [s for s in r.fin["diluted_shares"][-10:] if s]
    if len(sh) < 2:
        return None
    return (sh[-1] / sh[0]) ** (1 / (len(sh) - 1)) - 1


def summary_table(results: list[Result]) -> str:
    rows = [
        "| Ticker | Price | OE/share | P/OE | Base IV | MoS | Base IRR | IRR, no re-rating | "
        "Needed yr-10 multiple | Quality | Total | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in results:
        base = next((c.ivps for c in r.cases if c.case == "base"), None)
        d = r.decision
        rows.append(
            f"| {r.ticker} | {_usd(r.price)} | {_usd(r.oeps)} | {_x(r.inputs.get('p_oe'))} | {_usd(base)} | "
            f"{_p(r.mos, 0)} | {_p(r.expected_return_irr)} | {_p(r.expected_return_no_rerating)} | "
            f"{_x(r.inputs.get('required_exit_multiple'))} | {d.quality if d.quality is not None else '—'} | "
            f"{d.total if d.total is not None else '—'} | {d.verdict} |"
        )
    return "\n".join(rows)
