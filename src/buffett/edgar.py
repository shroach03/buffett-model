"""SEC EDGAR access: ticker -> CIK, companyfacts download with caching.

The SEC publishes every XBRL-tagged number from every filing as JSON at
https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json. There is no
scraping involved. The SEC's fair-access rules require a descriptive
User-Agent (name + email) and fewer than 10 requests per second.

Two loaders share one schema:
  * ``fetch_companyfacts`` hits the live API (cached to disk per day).
  * ``load_snapshot`` reads the gzipped snapshots in ``data/fixtures``, which
    are the same JSON filtered to 10-K facts, so tests run offline and the
    results in the README are reproducible.
"""
from __future__ import annotations

import gzip
import json
import os
import time
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "data" / "fixtures"
CACHE = Path(os.environ.get("BUFFETT_CACHE", REPO_ROOT / ".cache"))

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

_MIN_INTERVAL = 0.15  # seconds between requests (~6.7 req/s, under the SEC's 10/s cap)
_last_request = 0.0


def _user_agent() -> str:
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua:
        raise RuntimeError(
            "Set SEC_USER_AGENT to 'Your Name your@email.com' (required by SEC fair-access rules)."
        )
    return ua


def _get_json(url: str) -> dict:
    import requests  # imported lazily so offline use needs no network deps

    global _last_request
    wait = _MIN_INTERVAL - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    resp = requests.get(url, headers={"User-Agent": _user_agent()}, timeout=30)
    _last_request = time.monotonic()
    resp.raise_for_status()
    return resp.json()


def _cached(name: str, url: str) -> dict:
    """Fetch ``url`` at most once per day; cache the raw JSON on disk."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.{date.today().isoformat()}.json.gz"
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    data = _get_json(url)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def ticker_to_cik(ticker: str) -> int:
    table = _cached("company_tickers", TICKERS_URL)
    for row in table.values():
        if row["ticker"].upper() == ticker.upper():
            return int(row["cik_str"])
    raise KeyError(f"Ticker {ticker!r} not found in SEC ticker table")


def fetch_companyfacts(ticker: str) -> dict:
    cik = ticker_to_cik(ticker)
    return _cached(f"companyfacts_{cik:010d}", FACTS_URL.format(cik=cik))


def load_snapshot(ticker: str) -> dict:
    path = FIXTURES / f"{ticker.upper()}.json.gz"
    if not path.exists():
        raise FileNotFoundError(f"No snapshot for {ticker} at {path}")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def load(ticker: str, live: bool = False) -> dict:
    return fetch_companyfacts(ticker) if live else load_snapshot(ticker)
