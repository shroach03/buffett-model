"""Command line: ``python -m buffett <command>``.

  analyze TICKER [--live] [--price P] [--no-judgment] [--out DIR]
  screen  TICKER [TICKER ...] [--live]        one-line-per-company summary table
  snapshot TICKER [TICKER ...]                save live SEC data as an offline fixture
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

from . import edgar, report
from .analysis import analyze


def _run(ticker, args):
    facts = edgar.load(ticker, live=args.live)
    return analyze(ticker, facts=facts, price=getattr(args, "price", None),
                   judgment=not getattr(args, "no_judgment", False))


def main(argv=None) -> int:
    # Briefs contain ×, −, ≥ etc.; Windows consoles default to a legacy codepage.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap =argparse.ArgumentParser(prog="buffett", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze")
    a.add_argument("ticker")
    a.add_argument("--live", action="store_true", help="fetch from SEC instead of the bundled snapshot")
    a.add_argument("--price", type=float)
    a.add_argument("--no-judgment", action="store_true", help="ignore data/judgment inputs")
    a.add_argument("--out", type=Path, help="write the brief to DIR/TICKER.md")
    s = sub.add_parser("screen")
    s.add_argument("tickers", nargs="+")
    s.add_argument("--live", action="store_true")
    n = sub.add_parser("snapshot")
    n.add_argument("tickers", nargs="+")
    args = ap.parse_args(argv)

    if args.cmd == "analyze":
        md = report.brief(_run(args.ticker, args))
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / f"{args.ticker.upper()}.md").write_text(md, encoding="utf-8", newline="\n")
        print(md)
    elif args.cmd == "screen":
        print(report.summary_table([_run(t, args) for t in args.tickers]))
    elif args.cmd == "snapshot":
        for t in args.tickers:
            facts = edgar.fetch_companyfacts(t)
            path = edgar.FIXTURES / f"{t.upper()}.json.gz"
            with gzip.open(path, "wt", encoding="utf-8") as f:
                json.dump(facts, f, separators=(",", ":"))
            print(f"saved {path}")
    return 0
