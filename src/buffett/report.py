"""Render an analysis Result as a Markdown opportunity brief."""
from __future__ import annotations

from .analysis import Result


def _m(x):
    return "n/a" if x is None else f"{x / 1e6:,.0f}"


def _p(x, d=1):
    return "n/a" if x is None else f"{x:.{d}%}"


def _usd(x):
    return "n/a" if x is None else f"${x:,.2f}"


def brief(r: Result) -> str:
    f, d = r.fin, r.decision
    fy = f.fy_labels()
    out = []
    price_line = f"{_usd(r.price)} ({r.price_date})" if r.price else "no price supplied"
    out.append(f"# {r.ticker} · {f.name.title()}\n")
    out.append(f"**Verdict: {d['verdict']}**, {d['reason']}  ")
    out.append(f"Latest annual data: {fy[-1]} 10-K (period ending {f.years[-1]}) · Price: {price_line}\n")
    if r.warnings:
        out.append("> " + "  \n> ".join("⚠ " + w for w in r.warnings) + "\n")

    # scorecard
    out.append("## Scorecard\n")
    out.append("| Category | Points | Max | Basis |\n|---|---:|---:|---|")
    j = r.judgment
    out.append(f"| Understandability & moat | {j.moat if j else '—'} | 15 | "
               f"{'judgment: ' + j.source if j else 'needs a judgment input'} |")
    for line in r.lines[:3]:
        out.append(f"| {line.category} | {line.points} | {line.max_points} | {line.basis} |")
    out.append(f"| Management & allocation | {j.management if j else '—'} | 10 | "
               f"{'judgment (see notes)' if j else 'needs a judgment input'}; share count "
               f"{_p(_share_cagr(r))}/yr over 10y |")
    q = d["quality"] if d["quality"] is not None else f"{d['quant_quality']} + judgment"
    out.append(f"| **Quality subtotal** (≥ 55) | **{q}** | 70 | |")
    for line in r.lines[3:]:
        out.append(f"| {line.category} | {line.points} | {line.max_points} | {line.basis} |")
    t = d["total"] if d["total"] is not None else "—"
    out.append(f"| **Total** (≥ 75) | **{t}** | 100 | |\n")
    fatal = d["fatal"] or ["none detected in the data"]
    out.append("**Fatal flaws:** " + "; ".join(fatal) + "\n")
    if j and j.notes:
        out.append(f"**Judgment notes ({j.date}):** {j.notes}\n")

    # expected return
    i = r.inputs
    out.append("## Expected return\n")
    if r.expected_return_irr is not None:
        out.append(
            f"- **Base-case 10-year IRR: {_p(r.expected_return_irr)}** vs {_p(0.10, 0)} hurdle. "
            f"Growth starts at g = b × ROIIC = {_p(i['b_base'])} × {_p(i['roiic_base'])} = {_p(i['g_base'])} "
            f"and fades to 2.5%; exit at the base case's own value, {i['base_exit_multiple']:.1f}× OE.")
        out.append(
            f"- Model shorthand: R ≈ b×ROIIC + (1−b)×OE/P + Δmultiple = {_p(i['b_base'])}×{_p(i['roiic_base'])} "
            f"+ {_p(1 - i['b_base'])}×{_p(1 / i['p_oe'])} + ({i['base_exit_multiple']:.1f}/{i['p_oe']:.1f})^(1/10)−1 "
            f"= **{_p(r.expected_return_eq)}** (holds year-one growth for all ten years, so it differs from the IRR).")
        out.append(
            f"- If the market keeps paying today's {i['p_oe']:.1f}× owner earnings in year ten: "
            f"{_p(r.expected_return_no_rerating)}.")
        rev = (f"justifying today's price takes {_p(r.reverse_dcf_g)} starting growth"
               if r.reverse_dcf_g is not None
               else f"no starting growth rate at the base-case ROIIC of {_p(i['roiic_base'])} justifies today's price")
        out.append(
            f"- Reverse DCF: to earn 10% from here, the market must pay **{i['required_exit_multiple']:.1f}× "
            f"owner earnings in year ten** (base case: {i['base_exit_multiple']:.1f}×). "
            f"Holding the base terminal assumptions instead, {rev}.\n")
    else:
        out.append("Not computable: " + ("no price" if not r.price else "missing owner earnings or returns") + "\n")

    # valuation cases
    if r.cases:
        out.append("## Intrinsic value (Model §10 DCF)\n")
        out.append(f"Normalized owner earnings {_m(r.normalized_oe)}M = {_usd(r.oeps)}/share; "
                   f"net debt excl. leases {_m(i['net_debt_dcf'])}M; {i['shares'] / 1e6:,.1f}M diluted shares.\n")
        out.append("| Case | r | Start g | Terminal g | ROIIC | IV/share | Terminal share | Exit multiple |")
        out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for c in r.cases:
            a = c["assumptions"]
            out.append(f"| {c['case']} | {_p(a.discount_rate, 0)} | {_p(a.g_start)} | {_p(a.g_terminal)} | "
                       f"{_p(a.roiic)} | {_usd(c['ivps'])} | {_p(c['terminal_share'], 0)} | "
                       f"{c['implied_exit_multiple']:.1f}× |")
        if r.mos is not None:
            out.append(f"\nMargin of safety vs base case: **{_p(r.mos, 0)}** (Model wants 20–30%).\n")

    if r.ladder:
        out.append("**Price ladder** (base-case 10-year return): " + " · ".join(
            f"{int(k * 100)}% → {_usd(v)}" for k, v in r.ladder.items()) + "\n")

    # ten-year table
    out.append("## Ten-year record (USD millions)\n")
    cols = ["FY", "Revenue", "Net income", "Owner earnings", "OE/share", "CFO−capex−SBC", "ROIC", "Diluted sh (M)"]
    out.append("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols))
    for k in range(max(0, len(fy) - 10), len(fy)):
        oeps = r.oe.oe_per_share[k]
        sh = f["diluted_shares"][k]
        out.append(
            f"| {fy[k]} | {_m(f['revenue'][k])} | {_m(f['net_income'][k])} | {_m(r.oe.owner_earnings[k])} | "
            f"{'n/a' if oeps is None else f'{oeps:.2f}'} | {_m(r.oe.conservative_fcf[k])} | {_p(r.ret.roic[k], 0)} | "
            f"{'n/a' if sh is None else f'{sh / 1e6:,.1f}'} |")
    c = r.cons
    out.append(
        f"\nConsistency tests: {c.positive_years}/{c.years_available} positive OE years · OEPS CAGR {_p(c.oeps_cagr)} · "
        f"{c.down_years} down years, worst {_p(c.worst_one_year_decline)} · longest recovery {c.longest_recovery_years}y · "
        f"cash conversion {c.cash_conversion:.2f}×\n" if c.cash_conversion else "")

    b = r.bs
    out.append("## Balance sheet (latest year)\n")
    out.append(f"Debt {_m(b.total_debt)}M + operating leases {_m(b.operating_leases)}M − excess cash "
               f"{_m(b.excess_cash)}M = net debt **{_m(b.net_debt)}M** "
               f"({'n/a' if b.net_debt_to_oe is None else f'{b.net_debt_to_oe:.2f}×'} OE; stressed "
               f"{'n/a' if b.stressed_net_debt_to_oe is None else f'{b.stressed_net_debt_to_oe:.2f}×'}). Coverage "
               f"{'no interest expense' if b.coverage is None else f'{b.coverage:,.0f}×'} "
               f"(stressed {'n/a' if b.stressed_coverage is None else f'{b.stressed_coverage:,.0f}×'}). "
               "Not testable from XBRL facts: pension deficits, supplier financing, guarantees, litigation, "
               "maturity schedule.\n")

    out.append("## Data provenance\n")
    out.append("Source: SEC XBRL company facts, 10-K and 10-K/A filings only. "
               f"{len(f.restatements)} restated values detected (latest filing used). Normalization notes:\n")
    for n in f.notes:
        out.append(f"- {n}")
    if r.ret.roiic_note:
        out.append(f"- ROIIC: {r.ret.roiic_note}")
    out.append("\n*Analysis for one individual's own decision, not investment advice. "
               "A CANDIDATE is a prompt to study, never an instruction to buy.*\n")
    return "\n".join(out)


def _share_cagr(r: Result):
    sh = [s for s in r.fin["diluted_shares"][-10:] if s]
    if len(sh) < 2:
        return None
    return (sh[-1] / sh[0]) ** (1 / (len(sh) - 1)) - 1


def summary_table(results: list[Result]) -> str:
    rows = ["| Ticker | Price | OE/share | P/OE | Base IV | MoS | Base IRR | IRR, no re-rating | "
            "Needed yr-10 multiple | Quality | Total | Verdict |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in results:
        base = next((c["ivps"] for c in r.cases if c["case"] == "base"), None)
        d = r.decision
        rows.append(
            f"| {r.ticker} | {_usd(r.price)} | {_usd(r.oeps)} | {r.inputs.get('p_oe', 0):.1f}× | {_usd(base)} | "
            f"{_p(r.mos, 0)} | {_p(r.expected_return_irr)} | {_p(r.expected_return_no_rerating)} | "
            f"{r.inputs.get('required_exit_multiple', 0):.1f}× | {d['quality'] if d['quality'] is not None else '—'} | "
            f"{d['total'] if d['total'] is not None else '—'} | {d['verdict']} |")
    return "\n".join(rows)
